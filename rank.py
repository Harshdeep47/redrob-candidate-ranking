"""
rank.py -- the compute-constrained ranking step.

This is the ONLY script subject to the hackathon's runtime budget:
  <= 5 minutes wall-clock, <= 16GB RAM, CPU-only, no network calls.

It loads precomputed artifacts (TF-IDF matrix, structured features) produced
by src/precompute.py, combines them into a single hybrid score per candidate,
and writes the top-100 ranked submission CSV in the exact format required by
submission_spec.docx.

Usage:
    python rank.py --candidates candidates.jsonl --artifacts artifacts/ --out submission.csv

If --artifacts is missing or stale (doesn't match --candidates), this script
will run precompute itself first -- see ensure_artifacts() below. This keeps
the single-command promise in the README ("python rank.py --candidates ...")
honest even though precompute is logically a separate, non-time-boxed stage.
"""
import argparse
import os
import sys
import time
import pickle

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity

from src.reasoning import build_reasoning

TOP_N = 100

# --- Hybrid score weights -----------------------------------------------
# These weights were chosen by reasoning about the JD's own stated priorities
# (see methodology writeup), not fit to the hidden ground truth (we don't have
# it). Semantic + skill fit dominates since the JD's central ask is technical
# fit; availability and behavioral signals matter but are explicitly framed
# by the JD as a *down-weighting* factor for otherwise-good candidates, not
# the primary driver.
W_SEMANTIC = 0.28
W_CORE_SKILL = 0.22
W_PRODUCTION = 0.16
W_EXPERIENCE = 0.10
W_AVAILABILITY = 0.12
W_LOCATION = 0.07
W_NOTICE = 0.05

# Multiplicative penalty terms (applied after the weighted sum, each in (0,1])
PENALTY_FIELDS = [
    "title_relevance_gate", "consulting_penalty", "architecture_penalty",
    "title_chaser_penalty", "cv_speech_penalty", "visa_gate_penalty",
]


def normalize(arr: np.ndarray) -> np.ndarray:
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-9:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def ensure_artifacts(candidates_path: str, artifacts_dir: str):
    needed = ["features.parquet", "candidate_tfidf.npz", "jd_tfidf.npz",
              "vectorizer.pkl", "candidate_order.csv", "source.meta.json"]
    missing = [f for f in needed if not os.path.exists(os.path.join(artifacts_dir, f))]

    stale = False
    if not missing:
        from src.precompute import file_fingerprint
        import orjson as _orjson
        with open(os.path.join(artifacts_dir, "source.meta.json"), "rb") as f:
            meta = _orjson.loads(f.read())
        current_fp = file_fingerprint(candidates_path)
        if meta.get("source_fingerprint") != current_fp:
            print("Cached artifacts were built from a different candidates file -- "
                  "regenerating to avoid ranking against stale data.")
            stale = True

    if missing or stale:
        if missing:
            print(f"Artifacts missing {missing}, running precompute first...")
        os.makedirs(artifacts_dir, exist_ok=True)
        from src import precompute
        sys.argv = ["precompute", "--candidates", candidates_path, "--out", artifacts_dir]
        precompute.main()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    ap.add_argument("--artifacts", default="artifacts", help="Directory with precomputed artifacts")
    ap.add_argument("--out", default="submission.csv", help="Output CSV path")
    args = ap.parse_args()

    t0 = time.time()
    ensure_artifacts(args.candidates, args.artifacts)

    # --- load precomputed artifacts (cheap, all local disk reads) ---
    feat_df = pd.read_parquet(os.path.join(args.artifacts, "features.parquet"))
    candidate_order = pd.read_csv(os.path.join(args.artifacts, "candidate_order.csv"))["candidate_id"]
    candidate_tfidf = sparse.load_npz(os.path.join(args.artifacts, "candidate_tfidf.npz"))
    jd_tfidf = sparse.load_npz(os.path.join(args.artifacts, "jd_tfidf.npz"))

    assert (feat_df["candidate_id"].values == candidate_order.values).all(), \
        "Row order mismatch between features.parquet and candidate_order.csv"

    print(f"Loaded artifacts in {time.time()-t0:.1f}s")

    # --- semantic similarity: candidate TF-IDF vs JD TF-IDF (cheap, vectorized) ---
    t1 = time.time()
    semantic_sim = cosine_similarity(candidate_tfidf, jd_tfidf).ravel()
    print(f"Computed semantic similarity for {len(semantic_sim)} candidates in {time.time()-t1:.1f}s")

    feat_df["semantic_sim"] = semantic_sim

    # --- normalize the continuous components that aren't already 0-1 ---
    feat_df["semantic_sim_norm"] = normalize(feat_df["semantic_sim"].values)
    feat_df["core_skill_norm"] = normalize(feat_df["core_skill_score"].values)
    feat_df["production_norm"] = feat_df["production_signal"]  # already 0-1
    feat_df["availability_norm"] = normalize(feat_df["availability"].values)

    # --- hybrid weighted score ---
    base_score = (
        W_SEMANTIC * feat_df["semantic_sim_norm"]
        + W_CORE_SKILL * feat_df["core_skill_norm"]
        + W_PRODUCTION * feat_df["production_norm"]
        + W_EXPERIENCE * feat_df["experience_fit"]
        + W_AVAILABILITY * feat_df["availability_norm"]
        + W_LOCATION * feat_df["location_fit"]
        + W_NOTICE * feat_df["notice_fit"]
    )

    penalty_multiplier = np.ones(len(feat_df))
    for field in PENALTY_FIELDS:
        penalty_multiplier *= feat_df[field].values

    final_score = base_score * penalty_multiplier

    # Honeypot / impossible-profile suppression: force to the very bottom of
    # the score range regardless of how good other features look. We don't
    # special-case-exclude them entirely (spec says we don't need to) -- we
    # just make sure no amount of keyword overlap can push them into the
    # top 100 by suppressing the score multiplicatively.
    final_score = np.where(feat_df["is_honeypot"].values, final_score * 0.01, final_score)

    feat_df["final_score"] = final_score

    # --- rank, take top N -- adapts to pool size so this also works on the
    # sandbox's small samples (<=100 candidates), not just the full 100K pool ---
    ranked = feat_df.sort_values(
        ["final_score", "candidate_id"], ascending=[False, True]
    ).reset_index(drop=True)
    top_n = min(TOP_N, len(ranked))
    top100 = ranked.head(top_n).copy()
    top100["rank"] = np.arange(1, top_n + 1)

    # Rescale score into the (0,1] display range expected by the sample
    # submission, while preserving strict ordering (ties broken by candidate_id
    # already, above).
    raw = top100["final_score"].values
    rmin, rmax = raw.min(), raw.max()
    if rmax - rmin < 1e-9:
        display_score = np.linspace(0.99, 0.40, top_n)
    else:
        display_score = 0.40 + 0.59 * (raw - rmin) / (rmax - rmin)
    # enforce non-increasing by construction (already sorted descending)
    top100["score"] = np.round(display_score, 4)

    # --- build reasoning strings from raw candidate records (need original text) ---
    print("Building reasoning strings...")
    t2 = time.time()
    reasoning_map = build_reasoning(args.candidates, set(top100["candidate_id"]), top100)
    top100["reasoning"] = top100["candidate_id"].map(reasoning_map)
    print(f"Reasoning built in {time.time()-t2:.1f}s")

    out_df = top100[["candidate_id", "rank", "score", "reasoning"]]
    out_df.to_csv(args.out, index=False)

    elapsed = time.time() - t0
    print(f"\nWrote {len(out_df)} rows to {args.out}")
    print(f"Total rank.py wall-clock time: {elapsed:.1f}s")
    if elapsed > 300:
        print("WARNING: exceeded the 5-minute ranking budget!")


if __name__ == "__main__":
    main()

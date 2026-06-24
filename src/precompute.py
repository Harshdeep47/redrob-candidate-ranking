"""
Precompute step (offline, NOT subject to the 5-minute ranking budget).

Reads candidates.jsonl once, computes:
  - structured features (features.py) for every candidate
  - a TF-IDF vectorizer fit on the full corpus (candidates + JD) and the
    resulting sparse matrix
  - cosine similarity of every candidate against the JD vector

...and writes everything to /artifacts as compact files (parquet + npz) that
rank.py loads in milliseconds. This step does the "expensive" work once;
rank.py only does cheap arithmetic over cached arrays, which is what keeps it
inside the 5-minute / 16GB / CPU-only / no-network ranking budget even for
a 100K-candidate pool.

Usage:
    python -m src.precompute --candidates /path/to/candidates.jsonl --out artifacts/
"""
import argparse
import time
import orjson
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from src.features import extract_features
from src.text_features import candidate_document, JD_TEXT_CLEAN


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    t0 = time.time()
    feature_rows = []
    documents = []
    candidate_ids = []

    print(f"Reading {args.candidates} ...")
    with open(args.candidates, "rb") as f:
        for i, line in enumerate(f):
            rec = orjson.loads(line)
            feature_rows.append(extract_features(rec))
            documents.append(candidate_document(rec))
            candidate_ids.append(rec["candidate_id"])
            if (i + 1) % 20000 == 0:
                print(f"  processed {i+1} candidates ({time.time()-t0:.1f}s)")

    n = len(candidate_ids)
    print(f"Done reading {n} candidates in {time.time()-t0:.1f}s")

    # --- structured features -> dataframe ---
    feat_df = pd.DataFrame(feature_rows)
    feat_df.to_parquet(f"{args.out}/features.parquet", index=False)
    print(f"Saved structured features: {feat_df.shape}")

    # --- TF-IDF over candidate docs + JD ---
    t1 = time.time()
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.6,
        sublinear_tf=True,
    )
    corpus = documents + [JD_TEXT_CLEAN]
    tfidf_matrix = vectorizer.fit_transform(corpus)
    candidate_matrix = tfidf_matrix[:-1]  # all but last row
    jd_vector = tfidf_matrix[-1]

    sparse.save_npz(f"{args.out}/candidate_tfidf.npz", candidate_matrix)
    sparse.save_npz(f"{args.out}/jd_tfidf.npz", jd_vector)

    import pickle
    with open(f"{args.out}/vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    print(f"TF-IDF fit + transform done in {time.time()-t1:.1f}s, matrix shape {candidate_matrix.shape}")

    # candidate_ids order must match row order of features.parquet AND candidate_tfidf.npz
    pd.Series(candidate_ids, name="candidate_id").to_csv(f"{args.out}/candidate_order.csv", index=False)

    print(f"\nTotal precompute time: {time.time()-t0:.1f}s")
    print(f"Artifacts written to {args.out}/")


if __name__ == "__main__":
    main()

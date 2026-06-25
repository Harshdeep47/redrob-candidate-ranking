"""
Streamlit sandbox app -- satisfies the hackathon's mandatory "sandbox / demo
link" requirement (spec section 10.5).

Purpose: a fast, low-stakes way for organizers (and you) to verify the
ranking system runs end-to-end on a small sample, before the real Stage 3
reproduction against the full 100K pool happens in Redrob's own sandbox.

Run locally:
    streamlit run app.py

Deploy: push this repo to GitHub, then create a new app at
https://streamlit.io/cloud pointing at this file. No secrets or API keys
needed -- the whole pipeline is local CPU compute.
"""
import io
import os
import sys
import tempfile
import time

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Redrob Candidate Ranker -- Sandbox", layout="wide")

st.title("Redrob Candidate Discovery & Ranking -- Sandbox")
st.markdown(
    """
This is the **small-sample reproducibility sandbox** for the Intelligent
Candidate Discovery & Ranking Challenge submission. It runs the exact same
`rank.py` pipeline used for the full 100,000-candidate submission, just
against whatever sample you upload here (≤100 candidates recommended for a
fast demo).

Upload a `candidates.jsonl` file (one JSON object per line, matching
`candidate_schema.json`) and click **Run ranking**.
"""
)

uploaded = st.file_uploader("Upload candidates.jsonl", type=["jsonl"])

col1, col2 = st.columns(2)
with col1:
    run_button = st.button("Run ranking", type="primary", disabled=uploaded is None)
with col2:
    st.caption("CPU-only, no GPU, no network calls during ranking -- matches the hackathon's compute constraints.")

if uploaded is not None:
    raw_bytes = uploaded.getvalue()
    n_lines = raw_bytes.count(b"\n") + (1 if raw_bytes and not raw_bytes.endswith(b"\n") else 0)
    st.info(f"Loaded file with approximately {n_lines} candidate record(s).")

if run_button and uploaded is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        candidates_path = os.path.join(tmpdir, "candidates.jsonl")
        with open(candidates_path, "wb") as f:
            f.write(raw_bytes)

        artifacts_dir = os.path.join(tmpdir, "artifacts")
        out_path = os.path.join(tmpdir, "submission.csv")
        os.makedirs(artifacts_dir, exist_ok=True)

        progress = st.empty()
        progress.info("Running precompute (feature extraction + TF-IDF)...")

        t0 = time.time()
        try:
            # Run precompute and rank as in-process calls so we can show
            # progress / timing directly in the Streamlit UI rather than
            # shelling out.
            from src import precompute as precompute_mod
            sys.argv = ["precompute", "--candidates", candidates_path, "--out", artifacts_dir]
            precompute_mod.main()

            progress.info("Precompute done. Running ranking step...")

            import rank as rank_mod
            sys.argv = ["rank", "--candidates", candidates_path,
                        "--artifacts", artifacts_dir, "--out", out_path]
            rank_mod.main()

            elapsed = time.time() - t0
            progress.success(f"Done in {elapsed:.1f} seconds (well under the 5-minute budget).")

            result_df = pd.read_csv(out_path)
            st.subheader(f"Ranked output ({len(result_df)} candidates)")
            st.dataframe(result_df, use_container_width=True)

            csv_buffer = io.StringIO()
            result_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "Download submission.csv",
                data=csv_buffer.getvalue(),
                file_name="submission.csv",
                mime="text/csv",
            )
        except Exception as e:
            progress.error(f"Ranking failed: {e}")
            st.exception(e)

st.divider()
st.markdown(
    """
**Full repo & methodology:** see the GitHub repository this sandbox is
deployed from for the full architecture writeup, the 100K-candidate run,
and the complete commit history showing iteration.
"""
)

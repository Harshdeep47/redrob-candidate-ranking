"""
main.py -- frontend for the AI candidate ranking engine.

A single-file Streamlit app: upload a candidate pool, click Run, and get
back the top-ranked candidates as readable cards plus a downloadable CSV.
This is a presentation layer on top of the real ranking pipeline in
precompute.py / rank.py -- nothing here is reimplemented or mocked.

Run it with:
    streamlit run main.py

Accepted input formats:
    .jsonl  -- one JSON object per line (native format, no conversion needed)
    .json   -- a single JSON array of candidate objects (auto-converted to
               .jsonl in memory before being handed to the pipeline)

Excel/CSV are intentionally not supported yet: each candidate record is a
nested structure (a list of past jobs, a list of skills, a dict of skill
test scores) that a flat spreadsheet row can't hold without losing
information or inventing a custom flattening convention. Revisit this if/
when a defined spreadsheet template is built.
"""
import contextlib
import html
import io
import os
import sys
import tempfile
import time
from datetime import datetime

import orjson
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

APP_NAME = "Talent Signal"
APP_TAGLINE = "Rank candidates the way a great recruiter reads a resume \u2014 not by keyword count."

if "run_history" not in st.session_state:
    st.session_state.run_history = []  # most recent last; rendered reversed
if "card_filter" not in st.session_state:
    st.session_state.card_filter = ""

st.set_page_config(page_title=APP_NAME, page_icon="\U0001F9ED", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1140px; }
#MainMenu, footer, header { visibility: hidden; }

.hero {
    position: relative; overflow: hidden;
    background: radial-gradient(circle at 15% 20%, #3a2a7a 0%, #1a1330 55%, #0e0a1c 100%);
    border-radius: 22px; padding: 2.6rem 2.8rem; margin-bottom: 1.8rem; color: white;
}
.hero::after {
    content: ""; position: absolute; top: -60px; right: -60px; width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(140,110,255,0.35), transparent 70%);
    border-radius: 50%;
}
.hero-logo {
    display: inline-flex; align-items: center; gap: .5rem; font-weight: 800; font-size: .95rem;
    letter-spacing: .02em; margin-bottom: 1.1rem; color: #C9B8FF;
}
.hero h1 {
    margin: 0 0 .5rem 0; font-size: 2.15rem; font-weight: 800; color: white; letter-spacing: -0.01em;
}
.hero p { margin: 0; opacity: .82; font-size: 1.04rem; max-width: 640px; line-height: 1.5; }
.hero .badges { margin-top: 1.3rem; display: flex; gap: .5rem; flex-wrap: wrap; }
.hero .badge {
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18);
    border-radius: 999px; padding: .3rem .85rem; font-size: .78rem; color: #DCD5F5;
}

.step-head { display: flex; align-items: center; gap: .65rem; margin: 0 0 .4rem 0; }
.step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.85rem; height: 1.85rem; border-radius: 50%; background: #4B2E9E;
    color: white; font-weight: 700; font-size: .85rem; flex-shrink: 0;
}
.step-title { font-size: 1.25rem; font-weight: 700; color: #1A1A2E; margin: 0; }
.step-sub { color: #6B6478; font-size: .92rem; margin: 0 0 1rem 2.5rem; }

.fmt-row { display: flex; gap: .5rem; margin: .5rem 0 1.1rem 2.5rem; flex-wrap: wrap; }
.fmt-chip {
    font-size: .76rem; font-weight: 600; padding: .25rem .65rem; border-radius: 7px;
    background: #EFEAFB; color: #4B2E9E; border: 1px solid #DCD1F7;
}
.fmt-chip.disabled { background: #F2F2F4; color: #A4A0AE; border-color: #E5E3E9; }

.card {
    border: 1px solid #E9E5F7; border-radius: 16px; padding: 1.15rem 1.35rem;
    margin-bottom: .8rem; background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(30,20,80,0.04);
}
.card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.rank-badge {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 2.3rem; height: 2.3rem; border-radius: 50%;
    background: linear-gradient(135deg, #5B3DC4, #4B2E9E); color: white;
    font-weight: 700; font-size: .88rem; flex-shrink: 0;
}
.rank-badge.top10 { background: linear-gradient(135deg, #E0922F, #C97A1A); }
.cand-name { font-weight: 700; font-size: 1.08rem; color: #1A1A2E; margin: 0; }
.cand-sub { color: #6B6478; font-size: .87rem; margin: .15rem 0 0 0; }
.score-chip {
    background: #F6F4FC; color: #4B2E9E; font-weight: 800; font-size: 1rem;
    border-radius: 9px; padding: .3rem .7rem; white-space: nowrap;
}
.reasoning { color: #45414F; font-size: .89rem; margin-top: .7rem; line-height: 1.5; }
.cand-id { color: #B2ABC7; font-size: .7rem; font-family: monospace; margin-top: .35rem; }

.stat-box {
    background: linear-gradient(150deg, #F8F6FD, #F0ECFA); border: 1px solid #E9E5F7;
    border-radius: 14px; padding: 1rem 1rem; text-align: center;
}
.stat-box .num { font-size: 1.6rem; font-weight: 800; color: #4B2E9E; line-height: 1.2; }
.stat-box .label { font-size: .76rem; color: #6B6478; margin-top: .15rem; }

.empty-state {
    border: 1.5px dashed #D9D2EE; border-radius: 14px; padding: 1.6rem;
    text-align: center; color: #8B85A0; font-size: .92rem; margin: 0 0 .5rem 2.5rem;
}

/* ---------- Sidebar: run history ---------- */
section[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }
.hist-empty {
    border: 1.5px dashed #3A3552; border-radius: 10px; padding: .9rem;
    text-align: center; color: #8B85A0; font-size: .8rem; margin-top: .3rem;
}
.hist-item {
    background: #211D38; border: 1px solid #34304F; border-radius: 10px;
    padding: .65rem .8rem; margin-bottom: .5rem;
}
.hist-item .hist-name { color: #E8E3F7; font-size: .82rem; font-weight: 600; margin: 0; }
.hist-item .hist-meta { color: #9089AE; font-size: .73rem; margin: .2rem 0 0 0; }
.hist-item .hist-score { color: #C9B8FF; font-weight: 700; }
.sidebar-foot { color: #8B85A0; font-size: .78rem; line-height: 1.5; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="hero">
    <div class="hero-logo">\U0001F9ED &nbsp;{APP_NAME.upper()}</div>
    <h1>AI-powered candidate ranking</h1>
    <p>{APP_TAGLINE}</p>
    <div class="badges">
        <div class="badge">CPU-only, no GPU required</div>
        <div class="badge">Runs fully offline / no network calls</div>
        <div class="badge">Verified skill data &gt; self-reported claims</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("##### \U0001F4CB Run history")
    if not st.session_state.run_history:
        st.markdown(
            '<div class="hist-empty">Your past runs will show up here \u2014 '
            'nothing yet this session.</div>',
            unsafe_allow_html=True,
        )
    else:
        for i, run in enumerate(reversed(st.session_state.run_history)):
            st.markdown(
                f"""
<div class="hist-item">
  <p class="hist-name">{html.escape(run['filename'])}</p>
  <p class="hist-meta">{run['timestamp']} &middot; {run['n_candidates']:,} candidates &middot; {run['elapsed']:.1f}s</p>
  <p class="hist-meta">Top score: <span class="hist-score">{run['top_score']}</span></p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.download_button(
                "Re-download CSV", data=run["csv_bytes"],
                file_name=f"ranked_candidates_{run['timestamp_safe']}.csv",
                mime="text/csv", key=f"hist_dl_{i}",
                use_container_width=True,
            )

    st.divider()
    st.markdown("##### \U0001F50D Filter results")
    st.session_state.card_filter = st.text_input(
        "Search by name, title, or company",
        value=st.session_state.card_filter,
        placeholder="e.g. Razorpay, NLP Engineer...",
        label_visibility="collapsed",
        disabled=not st.session_state.run_history,
    )
    if not st.session_state.run_history:
        st.caption("Available once you have at least one run.")

    st.divider()
    st.markdown(
        '<p class="sidebar-foot">Job-title relevance and verified skill scores '
        'outrank keyword overlap, and disqualifying conditions multiply the score '
        'down rather than just subtracting points. Full writeup: '
        '<code>explainer/</code> in the repo.</p>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="step-head"><div class="step-num">1</div><div class="step-title">Upload your candidate pool</div></div>
<p class="step-sub">One record per candidate, with career history, skills, and any platform signals you track.</p>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="fmt-row">
    <div class="fmt-chip">.jsonl &mdash; one JSON object per line</div>
    <div class="fmt-chip">.json &mdash; a single JSON array</div>
    <div class="fmt-chip disabled">.xlsx / .csv &mdash; coming soon</div>
</div>
""",
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Upload candidates",
    type=["jsonl", "json"],
    label_visibility="collapsed",
    help="Large files (the full dataset can be several hundred MB) take a little while to "
         "transfer over the browser before processing even starts -- that's normal.",
)

n_candidates = None
candidates_jsonl_bytes = None
upload_error = None

if uploaded is not None:
    with st.spinner(f"Receiving {uploaded.name} ({uploaded.size / (1024*1024):.1f} MB)..."):
        raw_bytes = uploaded.getvalue()

    if uploaded.name.lower().endswith(".jsonl"):
        candidates_jsonl_bytes = raw_bytes
        n_candidates = raw_bytes.count(b"\n") + (1 if raw_bytes and not raw_bytes.endswith(b"\n") else 0)
    else:
        try:
            parsed = orjson.loads(raw_bytes)
            if not isinstance(parsed, list):
                upload_error = (
                    "This .json file doesn't contain a JSON array at the top level "
                    "(expected a list of candidate objects, like [{...}, {...}, ...])."
                )
            else:
                lines = [orjson.dumps(obj) for obj in parsed]
                candidates_jsonl_bytes = b"\n".join(lines) + b"\n"
                n_candidates = len(parsed)
        except Exception as e:
            upload_error = f"Couldn't parse this as JSON: {e}"

    if upload_error:
        st.error(upload_error)
    else:
        size_mb = len(candidates_jsonl_bytes) / (1024 * 1024)
        st.success(f"Ready: **{n_candidates:,}** candidate record(s) ({size_mb:.1f} MB).")
        if n_candidates and n_candidates > 5000:
            st.info(
                "Large pool detected. The one-time feature/index build will take roughly "
                "40\u201380 seconds for a dataset this size; the actual ranking step after that "
                "finishes in just a few seconds."
            )
else:
    st.markdown(
        '<div class="empty-state">No file uploaded yet \u2014 drag a .jsonl or .json file above to get started.</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="step-head"><div class="step-num">2</div><div class="step-title">Run the ranking</div></div>
""",
    unsafe_allow_html=True,
)
run_button = st.button(
    "Run ranking", type="primary",
    disabled=(uploaded is None or candidates_jsonl_bytes is None),
)


class StreamToStatus:
    """Redirects stdout lines into a live-updating Streamlit status box,
    so the person watching sees real progress (batch counts, timings) from
    inside precompute.py / rank.py instead of one static spinner."""

    def __init__(self, status_widget):
        self.status_widget = status_widget

    def write(self, text):
        text = text.strip()
        if text:
            self.status_widget.write(text)

    def flush(self):
        pass


def load_display_fields(candidates_path: str, wanted_ids: set) -> dict:
    """Stream the candidates file once to pull a few human-readable fields
    (name, title, company, location) for the candidates that made the final
    ranked list, purely for nicer card display -- the ranking itself never
    depends on this."""
    out = {}
    with open(candidates_path, "rb") as f:
        for line in f:
            if not line.strip():
                continue
            rec = orjson.loads(line)
            cid = rec.get("candidate_id")
            if cid in wanted_ids:
                p = rec.get("profile", {})
                out[cid] = {
                    "name": p.get("anonymized_name", "Unknown"),
                    "title": p.get("current_title", ""),
                    "company": p.get("current_company", ""),
                    "location": p.get("location", ""),
                }
            if len(out) == len(wanted_ids):
                break
    return out


def render_cards(result_df: pd.DataFrame, display_fields: dict, filter_text: str = ""):
    filter_text = (filter_text or "").strip().lower()
    shown = 0
    for _, row in result_df.iterrows():
        cid = row["candidate_id"]
        info = display_fields.get(cid, {})
        name_raw = str(info.get("name", cid))
        title_raw = str(info.get("title", ""))
        company_raw = str(info.get("company", ""))
        location_raw = str(info.get("location", ""))

        if filter_text:
            haystack = f"{name_raw} {title_raw} {company_raw} {location_raw}".lower()
            if filter_text not in haystack:
                continue

        shown += 1
        name = html.escape(name_raw)
        title = html.escape(title_raw)
        company = html.escape(company_raw)
        location = html.escape(location_raw)
        subtitle = " &middot; ".join(x for x in [title, company, location] if x)
        rank = int(row["rank"])
        badge_class = "rank-badge top10" if rank <= 10 else "rank-badge"
        score = html.escape(str(row.get("score", "")))
        reasoning = html.escape(str(row.get("reasoning", "")))
        cid_safe = html.escape(str(cid))

        st.markdown(
            f"""
<div class="card">
  <div class="card-top">
    <div style="display:flex; gap:.9rem; align-items:flex-start;">
      <div class="{badge_class}">{rank}</div>
      <div>
        <p class="cand-name">{name}</p>
        <p class="cand-sub">{subtitle}</p>
      </div>
    </div>
    <div class="score-chip">{score}</div>
  </div>
  <p class="reasoning">{reasoning}</p>
  <p class="cand-id">{cid_safe}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    if filter_text and shown == 0:
        st.info(f"No candidates match \u201c{filter_text}\u201d.")
    elif filter_text:
        st.caption(f"Showing {shown} of {len(result_df)} candidates matching \u201c{filter_text}\u201d.")


if run_button and candidates_jsonl_bytes is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        candidates_path = os.path.join(tmpdir, "candidates.jsonl")
        with open(candidates_path, "wb") as f:
            f.write(candidates_jsonl_bytes)

        artifacts_dir = os.path.join(tmpdir, "artifacts")
        out_path = os.path.join(tmpdir, "submission.csv")
        os.makedirs(artifacts_dir, exist_ok=True)

        t0 = time.time()
        status = st.status("Starting pipeline...", expanded=True)
        stream = StreamToStatus(status)

        try:
            with contextlib.redirect_stdout(stream):
                from src import precompute as precompute_mod
                sys.argv = ["precompute", "--candidates", candidates_path, "--out", artifacts_dir]
                precompute_mod.main()

                import rank as rank_mod
                sys.argv = ["rank", "--candidates", candidates_path,
                            "--artifacts", artifacts_dir, "--out", out_path]
                rank_mod.main()

            elapsed = time.time() - t0
            status.update(label=f"Done in {elapsed:.1f}s", state="complete", expanded=False)

            result_df = pd.read_csv(out_path)
            display_fields = load_display_fields(candidates_path, set(result_df["candidate_id"]))

            st.markdown(
                """
<div class="step-head"><div class="step-num">3</div><div class="step-title">Results</div></div>
""",
                unsafe_allow_html=True,
            )

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="stat-box"><div class="num">{len(result_df)}</div>'
                             f'<div class="label">candidates ranked</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-box"><div class="num">{elapsed:.1f}s</div>'
                             f'<div class="label">ranking wall-clock</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-box"><div class="num">{n_candidates:,}</div>'
                             f'<div class="label">candidates considered</div></div>', unsafe_allow_html=True)
            with c4:
                top_score = result_df["score"].iloc[0] if len(result_df) else "-"
                st.markdown(f'<div class="stat-box"><div class="num">{top_score}</div>'
                             f'<div class="label">top match score</div></div>', unsafe_allow_html=True)

            st.write("")
            tab_cards, tab_table = st.tabs(["Candidate cards", "Raw table"])

            with tab_cards:
                render_cards(result_df, display_fields, st.session_state.card_filter)

            with tab_table:
                st.dataframe(result_df, use_container_width=True, hide_index=True)

            csv_buffer = io.StringIO()
            result_df.to_csv(csv_buffer, index=False)
            csv_text = csv_buffer.getvalue()

            run_dt = datetime.now()
            st.session_state.run_history.append({
                "filename": uploaded.name,
                "timestamp": run_dt.strftime("%b %d, %H:%M"),
                "timestamp_safe": run_dt.strftime("%Y%m%d_%H%M%S"),
                "n_candidates": n_candidates,
                "elapsed": elapsed,
                "top_score": top_score,
                "csv_bytes": csv_text,
            })
            st.session_state.run_history = st.session_state.run_history[-8:]  # cap history length

            st.download_button(
                "Download results as CSV",
                data=csv_text,
                file_name="ranked_candidates.csv",
                mime="text/csv",
                type="primary",
            )

        except Exception as e:
            status.update(label="Ranking failed", state="error")
            st.error(f"Something went wrong: {e}")
            st.exception(e)

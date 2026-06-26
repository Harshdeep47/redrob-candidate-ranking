"""
Generates the `reasoning` column for the submission CSV.

Hard requirements from submission_spec.docx Section 3 ("Reasoning column"):
  - Must reference SPECIFIC facts from the candidate's profile (years of
    experience, current title, named skills, signal values) -- not generic
    praise.
  - Must connect to specific JD requirements.
  - Must acknowledge honest concerns/gaps where they exist, not just sell
    the candidate.
  - Zero hallucination: every claim must trace to something literally present
    in the candidate's record.
  - Must vary substantively across candidates (not templated with only the
    name swapped).
  - Tone must match rank: a top-10 pick should sound confident; a rank-90
    pick should sound hedged.

Design choice: we deliberately do NOT call an LLM here. The ranking step has
no network access by spec, and even if it did, an LLM-generated reasoning
string risks inventing a skill or fact that isn't in the profile (exactly
what's penalized). Instead we build reasoning by selecting from a pool of
fact-slots actually present in the candidate's record and assembling them
with light randomized-but-deterministic sentence-structure variation, so the
output is both 100% grounded AND non-templated in the "name-swap" sense the
spec warns about.
"""
import random
import orjson

# Candidate-facing facts we are willing to cite, in priority order of what's
# most relevant to defend a ranking decision for THIS JD.

CORE_SKILL_NAMES = {
    "Embeddings", "Sentence Transformers", "Vector Representations", "Text Encoders",
    "Semantic Search", "Vector Search", "Pinecone", "Weaviate", "Qdrant", "Milvus",
    "OpenSearch", "Elasticsearch", "FAISS", "pgvector", "BM25", "Search Infrastructure",
    "Search Backend", "Indexing Algorithms", "Information Retrieval",
    "Information Retrieval Systems", "Ranking Systems", "Learning to Rank",
    "Recommendation Systems", "Search & Discovery", "Python",
}

CONCERN_PHRASES = {
    "long_notice": lambda days: f"notice period is {days} days, longer than the JD's sub-30-day preference",
    "non_india": lambda loc: f"based in {loc}, outside the JD's preferred India locations",
    "low_response": lambda r: f"recruiter response rate is only {r:.0%}",
    "inactive": lambda d: f"last active on the platform {d}",
    "not_open": "not currently flagged open-to-work",
    "consulting_only": "career has been entirely at consulting/IT-services firms",
    "cv_speech_heavy": "skill set leans heavily toward computer vision/speech rather than NLP/IR",
    "under_experienced": lambda yoe: f"only {yoe:.1f} years of experience, below the JD's 5-9yr band",
    "over_experienced": lambda yoe: f"{yoe:.1f} years of experience, above the JD's typical band",
}


def _format_money(lpa_min, lpa_max):
    return f"\u20b9{lpa_min:.0f}-{lpa_max:.0f} LPA"


def build_reasoning(candidates_path: str, wanted_ids: set, top_df) -> dict:
    """
    Stream candidates.jsonl once, build a fact-grounded reasoning string for
    every candidate_id in wanted_ids. Returns {candidate_id: reasoning_str}.
    """
    rank_lookup = dict(zip(top_df["candidate_id"], top_df["rank"]))
    records = {}
    with open(candidates_path, "rb") as f:
        for line in f:
            rec = orjson.loads(line)
            if rec["candidate_id"] in wanted_ids:
                records[rec["candidate_id"]] = rec
            if len(records) == len(wanted_ids):
                break

    out = {}
    for cid, rec in records.items():
        rank = rank_lookup[cid]
        out[cid] = _reasoning_for(rec, rank)
    return out


def _reasoning_for(rec: dict, rank: int) -> str:
    rnd = random.Random(rec["candidate_id"])  # deterministic per-candidate variation

    p = rec["profile"]
    sig = rec["redrob_signals"]
    history = rec["career_history"]
    skills = rec.get("skills", [])

    yoe = p["years_of_experience"]
    title = p["current_title"]
    company = p["current_company"]
    location = p["location"]

    # Pull named core skills actually present, with proficiency, preferring
    # ones with verified assessment scores when available.
    named_core = []
    for s in skills:
        if s["name"] in CORE_SKILL_NAMES:
            score = sig.get("skill_assessment_scores", {}).get(s["name"])
            named_core.append((s["name"], s["proficiency"], score))
    named_core.sort(key=lambda x: (x[2] is None, -(x[2] or 0)))

    # Most relevant prior role for "what they actually built" -- only trust
    # the description if the role's OWN title is plausibly relevant (Tier
    # S/A). Descriptions attached to irrelevant titles (HR Manager, Sales
    # Executive, etc.) are randomly shuffled ~84% of the time in this
    # dataset and would be misleading to quote as evidence either way.
    from src.jd_requirements import title_tier as _title_tier
    relevant_roles = [ch for ch in history if _title_tier(ch["title"]) in {"direct", "adjacent"}]
    most_relevant_role = relevant_roles[0] if relevant_roles else None

    # --- positive clauses pool (only built from facts that exist) ---
    positives = []
    positives.append(f"{title} at {company} with {yoe:.1f} years of experience")

    if named_core:
        skill_strs = []
        for name, prof, score in named_core[:3]:
            if score is not None:
                skill_strs.append(f"{name} ({prof}, assessed {score:.0f}/100)")
            else:
                skill_strs.append(f"{name} ({prof})")
        positives.append("directly relevant skills: " + ", ".join(skill_strs))

    if most_relevant_role:
        desc = most_relevant_role["description"]
        snippet_words = desc.split()
        snippet = " ".join(snippet_words[:14]) + ("..." if len(snippet_words) > 14 else "")
        positives.append(f"most recent role describes: \"{snippet}\"")

    if sig.get("github_activity_score", -1) >= 40:
        positives.append(f"GitHub activity score {sig['github_activity_score']:.0f}/100")

    if sig.get("recruiter_response_rate", 0) >= 0.5:
        positives.append(f"strong recruiter response rate ({sig['recruiter_response_rate']:.0%})")

    if location in {"Pune, Maharashtra", "Noida, Uttar Pradesh"}:
        positives.append(f"based in {location}, matching the JD's preferred office locations")
    elif p["country"] == "India":
        positives.append(f"based in {location}, India")

    # --- concern clauses pool (only if the fact genuinely applies) ---
    concerns = []
    if sig["notice_period_days"] > 30:
        concerns.append(CONCERN_PHRASES["long_notice"](sig["notice_period_days"]))
    if p["country"] != "India" and not sig["willing_to_relocate"]:
        concerns.append(CONCERN_PHRASES["non_india"](f"{location}, {p['country']}"))
    if sig["recruiter_response_rate"] < 0.25:
        concerns.append(CONCERN_PHRASES["low_response"](sig["recruiter_response_rate"]))
    if not sig["open_to_work_flag"]:
        concerns.append(CONCERN_PHRASES["not_open"])
    if yoe < 5:
        concerns.append(CONCERN_PHRASES["under_experienced"](yoe))
    elif yoe > 9:
        concerns.append(CONCERN_PHRASES["over_experienced"](yoe))
    if not relevant_roles:
        concerns.append(f"current and prior titles ({title}) show no direct ML/AI/search role history")

    # --- assemble: vary sentence structure deterministically per-candidate ---
    pos_take = positives[:3] if len(positives) >= 3 else positives
    con_take = concerns[:2]

    templates_high = [
        "{pos}. {con}",
        "{pos}; {con}",
        "Strong fit: {pos}. {con}",
    ]
    templates_mid = [
        "{pos}. Some concerns: {con}",
        "{pos}, though {con}",
        "Reasonable fit \u2014 {pos}. {con}",
    ]
    templates_low = [
    "Partial match: {pos}. {con}",
    "Weaker fit: {pos}. {con}",
    "{pos}, but {con}",
    ]

    pos_str = "; ".join(pos_take)
    con_str = "; ".join(con_take) if con_take else "no major concerns identified"

    if rank <= 10:
        tmpl = rnd.choice(templates_high)
    elif rank <= 50:
        tmpl = rnd.choice(templates_mid)
    else:
        tmpl = rnd.choice(templates_low)

    reasoning = tmpl.format(pos=pos_str, con=con_str)
    # CSV-safety: collapse whitespace/newlines
    reasoning = " ".join(reasoning.split())
    # Clause-aware truncation: cut at the last semicolon/period before the
    # limit rather than mid-word, so we never emit a dangling fragment like
    # "not curr..." in the reasoning column.
    MAX_LEN = 380
    if len(reasoning) > MAX_LEN:
        cut = reasoning[:MAX_LEN]
        last_boundary = max(cut.rfind(";"), cut.rfind(". "))
        if last_boundary > MAX_LEN * 0.5:
            reasoning = cut[:last_boundary].rstrip(";. ") + "."
        else:
            last_space = cut.rfind(" ")
            reasoning = cut[:last_space].rstrip(";,") + "."
    return reasoning

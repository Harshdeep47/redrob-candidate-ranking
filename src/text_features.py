"""
Builds the text representation used for semantic (TF-IDF cosine) similarity
between the JD and each candidate.

We deliberately use TF-IDF + cosine similarity rather than a neural embedding
model (e.g. sentence-transformers). Reasons, in order of importance:

1. Compute constraints: ranking must run CPU-only, no GPU, <=5 min wall-clock,
   <=16GB RAM, for the FULL 100K candidate pool, reproduced in a sandboxed
   Docker container at Stage 3. A scikit-learn TfidfVectorizer fits this
   constraint trivially and has zero exotic dependencies (no torch/CUDA stack)
   to worry about breaking in a clean container rebuild.
2. The domain vocabulary here is fairly specific and closed (133 known skills,
   a fixed set of company/industry names, a narrow JD). TF-IDF on n-grams
   captures "RAG", "vector search", "production deployment" style phrase
   overlap perfectly well for this purpose; we are not doing open-domain
   semantic search over arbitrary natural language.
3. It keeps the system auditable: at the Stage 5 "defend your work" interview,
   every similarity score traces back to explicit shared terms, which is
   easier to defend than "the neural net said so."

The JD parsing into structured requirements (jd_requirements.py) does the heavy
lifting of capturing what the JD *means*; this TF-IDF layer captures textual/
semantic overlap as a complementary signal, not the primary one.
"""
import re

STOPWORD_EXTRA = {
    "year", "years", "experience", "company", "team", "work", "worked", "working",
    "role", "project", "projects", "using", "used", "build", "built", "building",
}
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./\- ]", " ", text)
    return text


def candidate_document(candidate: dict) -> str:
    """Concatenate the candidate's text-bearing fields into one document for TF-IDF."""

    p = candidate["profile"]

    parts = [
        p.get("headline", ""),
        p.get("summary", ""),
        p.get("current_title", ""),
        p.get("current_industry", ""),
    ]

    for ch in candidate.get("career_history", []):
        parts.append(ch.get("title", ""))
        parts.append(ch.get("description", ""))
        parts.append(ch.get("industry", ""))

    # Skill weighting
    for s in candidate.get("skills", []):
        skill = s.get("name", "")
        prof = s.get("proficiency", "").lower()

        if prof in ("expert", "advanced"):
            parts.extend([skill] * 3)
        elif prof == "intermediate":
            parts.extend([skill] * 2)
        else:
            parts.append(skill)

    # Certifications
    for cert in candidate.get("certifications", []):
        parts.append(cert.get("name", ""))

    # Education
    for edu in candidate.get("education", []):
        parts.append(edu.get("degree", ""))
        parts.append(edu.get("field", ""))

    # Languages
    for lang in candidate.get("languages", []):
        if isinstance(lang, dict):
            parts.append(lang.get("name", ""))
        else:
            parts.append(str(lang))

    return clean_text(" ".join(parts))


# JD text condensed to the parts that matter for semantic matching: the
# "what you'd actually be doing" + "things you absolutely need" + "how to
# read between the lines" sections. We exclude the meta-commentary (the
# "let's be honest" framing, logistics) since that's not skill/experience
# content and would just dilute the TF-IDF vector.
JD_TEXT = """
Own the intelligence layer of the product: ranking, retrieval, and matching
systems that decide what recruiters see when they search for candidates and
what candidates see when they search for roles. Audit existing BM25 and
rule-based scoring. Ship a v2 ranking system using embeddings, hybrid
retrieval, and LLM-based re-ranking. Set up evaluation infrastructure:
offline benchmarks, online A/B testing, recruiter feedback loops.

Production experience with embeddings-based retrieval systems: sentence
transformers, OpenAI embeddings, BGE, E5. Handled embedding drift, index
refresh, retrieval quality regression in production. Production experience
with vector databases or hybrid search infrastructure: Pinecone, Weaviate,
Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS. Strong Python, code
quality. Evaluation frameworks for ranking systems: NDCG, MRR, MAP,
offline to online correlation, A/B test interpretation.

LLM fine-tuning LoRA QLoRA PEFT. Learning to rank models XGBoost neural.
HR-tech recruiting tech marketplace products. Distributed systems
large-scale inference optimization. Open-source contributions AI ML.

Has shipped at least one end-to-end ranking search or recommendation system
to real users at meaningful scale. Strong opinions about retrieval hybrid
versus dense, evaluation offline versus online, LLM integration fine-tune
versus prompt. Applied machine learning AI roles at product companies, not
pure services. Recommendation system search system ranking system natural
language processing information retrieval semantic search vector search.
"""

JD_TEXT_CLEAN = clean_text(JD_TEXT)

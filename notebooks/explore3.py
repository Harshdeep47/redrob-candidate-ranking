"""
Key discovery: career_history[].description text is only reliably topic-matched
to career_history[].title for ML/AI-relevant titles. For common non-tech titles,
the description appears to be drawn from an unrelated/shuffled pool ~84% of the
time. This finding directly shaped title_relevance_gate() and the title-gated
version of production_signal_score() in src/features.py -- title, not free text,
has to be the dominant signal for whether a candidate's experience is relevant.
"""
import orjson

PATH = "/mnt/user-data/uploads/candidates.jsonl"

NON_TECH_TITLE_KEYWORDS = {
    "hr manager": ["hiring", "recruit", "onboard", "employee", "talent", "hr ", "performance review"],
    "sales executive": ["sales", "quota", "client", "deal", "revenue", "pipeline", "crm"],
    "accountant": ["ledger", "tax", "audit", "reconcil", "financial statement", "bookkeep"],
    "content writer": ["content", "article", "seo", "writing", "editorial", "blog"],
    "mechanical engineer": ["cad", "solidworks", "mechanical", "fea", "prototype", "manufactur"],
}

ML_TITLE_KEYWORDS = [
    "model", "embedding", "vector", "ranking", "retrieval", "rag", "llm", "ml ",
    "machine learning", "nlp", "search", "recommendation", "pipeline", "deploy",
    "production", "inference", "training data", "fine-tun", "feature", "dataset",
    "algorithm", "neural", "transform",
]

ML_TITLES = {
    "ml engineer", "ai engineer", "data scientist", "nlp engineer", "applied scientist",
    "machine learning engineer", "ai research", "ai specialist",
}


def main():
    checked_nontech, mismatch_nontech = 0, 0
    checked_ml, mismatch_ml = 0, 0

    with open(PATH, "rb") as f:
        for line in f:
            rec = orjson.loads(line)
            for ch in rec["career_history"]:
                t = ch["title"].lower()
                desc = ch["description"].lower()

                if t in NON_TECH_TITLE_KEYWORDS:
                    checked_nontech += 1
                    if not any(kw in desc for kw in NON_TECH_TITLE_KEYWORDS[t]):
                        mismatch_nontech += 1

                if any(k in t for k in ML_TITLES):
                    checked_ml += 1
                    if not any(kw in desc for kw in ML_TITLE_KEYWORDS):
                        mismatch_ml += 1

    print(f"Non-tech titles checked: {checked_nontech}, "
          f"description mismatch rate: {100*mismatch_nontech/checked_nontech:.1f}%")
    print(f"ML titles checked: {checked_ml}, "
          f"description mismatch rate: {100*mismatch_ml/checked_ml:.1f}%")
    print()
    print("Conclusion: description text can be trusted as evidence when the role's")
    print("OWN title is already ML/AI-relevant, but cannot be trusted to GRANT")
    print("relevance to an otherwise-irrelevant title. Title must gate description use.")


if __name__ == "__main__":
    main()

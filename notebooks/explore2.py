"""Deeper exploration: AI/ML relevant titles, skill vocabulary, honeypot patterns."""
import orjson
import collections

PATH = "/mnt/user-data/uploads/candidates.jsonl"

ml_titles = collections.Counter()
sample_honeypot_like = []

n = 0
with open(PATH, "rb") as f:
    for line in f:
        n += 1
        rec = orjson.loads(line)
        p = rec["profile"]
        title = p["current_title"].lower()
        if any(k in title for k in ["ml", "ai ", "machine learning", "data scien", "research scien",
                                      "applied scien", "nlp", "ai engineer", "ai/ml"]):
            ml_titles[p["current_title"]] += 1

        skills = rec.get("skills", [])
        expert_zero_duration = sum(1 for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 1) == 0)
        if expert_zero_duration >= 2:
            sample_honeypot_like.append(rec["candidate_id"])

n_total = n
print(f"Total: {n_total}\n")

print("=== Titles containing ML/AI/data-science keywords ===")
for t, c in ml_titles.most_common(40):
    print(f"  {t}: {c}")

print(f"\n=== Candidates with >=2 'expert + 0 duration_months' skills (potential honeypot signal) ===")
print(f"Count: {len(sample_honeypot_like)}")
print(sample_honeypot_like[:20])

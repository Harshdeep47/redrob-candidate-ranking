"""Initial exploration of candidates.jsonl - run once, print stats."""
import orjson
import collections

PATH = "/mnt/user-data/uploads/candidates.jsonl"

n = 0
countries = collections.Counter()
locations = collections.Counter()
current_titles = collections.Counter()
tiers = collections.Counter()
skill_names = collections.Counter()
yoe_bucket = collections.Counter()
open_to_work = collections.Counter()
github_missing = 0
offer_missing = 0
notice_periods = []
salary_mins = []
last_active_years = collections.Counter()

with open(PATH, "rb") as f:
    for line in f:
        n += 1
        rec = orjson.loads(line)
        p = rec["profile"]
        countries[p["country"]] += 1
        locations[p["location"]] += 1
        current_titles[p["current_title"]] += 1
        yoe = p["years_of_experience"]
        yoe_bucket[int(yoe)] += 1
        for edu in rec.get("education", []):
            tiers[edu.get("tier", "unknown")] += 1
        for s in rec.get("skills", []):
            skill_names[s["name"]] += 1
        sig = rec["redrob_signals"]
        open_to_work[sig["open_to_work_flag"]] += 1
        if sig["github_activity_score"] == -1:
            github_missing += 1
        if sig["offer_acceptance_rate"] == -1:
            offer_missing += 1
        notice_periods.append(sig["notice_period_days"])
        salary_mins.append(sig["expected_salary_range_inr_lpa"]["min"])
        last_active_years[sig["last_active_date"][:7]] += 1  # year-month

print(f"Total candidates: {n}\n")

print("=== Top 20 countries ===")
for c, cnt in countries.most_common(20):
    print(f"  {c}: {cnt}")

print("\n=== Top 25 locations ===")
for c, cnt in locations.most_common(25):
    print(f"  {c}: {cnt}")

print("\n=== Top 20 current titles ===")
for c, cnt in current_titles.most_common(20):
    print(f"  {c}: {cnt}")

print("\n=== Education tiers ===")
for t, cnt in tiers.most_common():
    print(f"  {t}: {cnt}")

print("\n=== Top 40 most common skills ===")
for s, cnt in skill_names.most_common(40):
    print(f"  {s}: {cnt}")

print(f"\n=== Years of experience distribution (bucketed) ===")
for y in sorted(yoe_bucket):
    print(f"  {y}: {yoe_bucket[y]}")

print(f"\n=== open_to_work_flag ===")
print(open_to_work)

print(f"\ngithub_activity_score == -1 (no github linked): {github_missing} ({100*github_missing/n:.1f}%)")
print(f"offer_acceptance_rate == -1 (no offer history): {offer_missing} ({100*offer_missing/n:.1f}%)")

print(f"\nnotice_period_days: min={min(notice_periods)}, max={max(notice_periods)}, mean={sum(notice_periods)/n:.1f}")
print(f"expected_salary min (LPA): min={min(salary_mins):.1f}, max={max(salary_mins):.1f}, mean={sum(salary_mins)/n:.1f}")

print(f"\n=== last_active_date distribution (top 15 year-months) ===")
for ym, cnt in sorted(last_active_years.items(), reverse=True)[:15]:
    print(f"  {ym}: {cnt}")

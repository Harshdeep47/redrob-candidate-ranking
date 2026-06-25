"""
Feature engineering for the Redrob candidate ranking system.

For each candidate, this module computes a dict of structured (non-text) features
that feed into the hybrid scorer in rank.py. Text fields (summary, career history
descriptions, skills) are handled separately via TF-IDF in the embeddings module --
this file is about everything else: experience fit, location fit, behavioral
signals, honeypot/sanity flags, and skill-taxonomy-based scoring.
"""
from datetime import date
from src.skill_taxonomy import skill_category
from src.jd_requirements import (
    LOCATION_TIER_A, LOCATION_TIER_B, COUNTRY_INDIA,
    EXPERIENCE_IDEAL_MIN, EXPERIENCE_IDEAL_MAX, EXPERIENCE_MIN_SOFT, EXPERIENCE_MAX_SOFT,
    EXPERIENCE_HARD_FLOOR, NOTICE_IDEAL_MAX_DAYS, NOTICE_ACCEPTABLE_MAX_DAYS,
    CONSULTING_FIRMS, NON_CODING_SENIOR_TITLES, TITLE_LADDER_WORDS,
    PRODUCTION_SIGNAL_PHRASES, RESEARCH_ONLY_SIGNAL_PHRASES, title_tier,
)

TODAY = date(2026, 6, 25)  # dataset's implied "now" -- last_active_date values cluster up to 2026-05


def _months_since(date_str: str) -> float:
    try:
        y, m, d = (int(x) for x in date_str.split("-"))
        return (TODAY.year - y) * 12 + (TODAY.month - m) + (TODAY.day - d) / 30.0
    except Exception:
        return 999.0


def experience_fit_score(yoe: float) -> float:
    """1.0 inside the ideal 6-8yr band, tapering off outside 5-9, sharper drop below the hard floor."""
    if EXPERIENCE_IDEAL_MIN <= yoe <= EXPERIENCE_IDEAL_MAX:
        return 1.0
    if EXPERIENCE_MIN_SOFT <= yoe <= EXPERIENCE_MAX_SOFT:
        return 0.85
    if yoe < EXPERIENCE_HARD_FLOOR:
        return 0.15
    if yoe < EXPERIENCE_MIN_SOFT:
        # 2-5 yrs: linear ramp from 0.15 -> 0.85
        return 0.15 + 0.7 * (yoe - EXPERIENCE_HARD_FLOOR) / (EXPERIENCE_MIN_SOFT - EXPERIENCE_HARD_FLOOR)
    # above 9 yrs: gentle taper down (overqualified isn't disqualifying, JD says band is soft)
    excess = yoe - EXPERIENCE_MAX_SOFT
    return max(0.5, 0.85 - 0.05 * excess)


def location_fit_score(country: str, location: str, willing_to_relocate: bool) -> float:
    if country == COUNTRY_INDIA:
        if location in LOCATION_TIER_A:
            return 1.0
        if location in LOCATION_TIER_B:
            return 0.9
        return 0.75  # other India Tier-1 cities (Bangalore, Chennai, Kolkata, etc.) -- relocation-plausible
    # Outside India: JD says "case-by-case, no visa sponsorship"
    return 0.25 if willing_to_relocate else 0.08


def notice_period_score(notice_days: int) -> float:
    if notice_days <= NOTICE_IDEAL_MAX_DAYS:
        return 1.0
    if notice_days <= NOTICE_ACCEPTABLE_MAX_DAYS:
        return 0.7
    if notice_days <= 90:
        return 0.45
    return 0.25


def consulting_only_penalty(career_history: list, current_industry: str, current_company: str) -> float:
    """
    JD: reject candidates who ONLY have consulting-firm experience. If currently at one but
    with prior product-company experience, that's fine -> no penalty in that case.
    Returns a multiplier (1.0 = no penalty, lower = bigger penalty).
    """
    def is_consulting(company, industry):
        if industry and industry.strip().lower() in {"it services", "consulting"}:
            return True
        if company and company.strip().lower() in CONSULTING_FIRMS:
            return True
        return False

    all_consulting = all(is_consulting(ch["company"], ch.get("industry", "")) for ch in career_history)
    if all_consulting:
        return 0.35  # meaningful penalty, not a hard zero -- some signal may still be useful
    return 1.0


def architecture_only_penalty(current_title: str, career_history: list) -> float:
    """
    JD: "if you're a senior engineer who hasn't written production code in the last 18 months
    because you moved into architecture/tech-lead roles, we will probably not move forward."
    Approximate via current title + recency of last individual-contributor-sounding role.
    """
    title_lower = current_title.lower()
    if any(w in title_lower for w in NON_CODING_SENIOR_TITLES):
        # check months since this role started; if long-tenured in a non-coding title, penalize
        current_role = next((ch for ch in career_history if ch.get("is_current")), None)
        if current_role:
            months_in_role = current_role.get("duration_months", 0)
            if months_in_role >= 18:
                return 0.5
    return 1.0


def title_chaser_penalty(career_history: list) -> float:
    """
    JD: title-ladder-climbing via company-hopping every ~1.5yrs is a red flag.
    Heuristic: 3+ jobs, each <=20 months, with titles showing ladder progression words.
    """
    if len(career_history) < 3:
        return 1.0
    short_stints = sum(1 for ch in career_history if ch.get("duration_months", 999) <= 20)
    ladder_titles = sum(
        1 for ch in career_history
        if any(w in ch["title"].lower() for w in TITLE_LADDER_WORDS)
    )
    if short_stints >= 3 and ladder_titles >= 2:
        return 0.6
    return 1.0


def production_signal_score(career_history: list) -> float:
    """
    JD's central ask: 'has shipped at least one end-to-end ranking/search/recommendation
    system to real users at meaningful scale.' Scan descriptions for production-deployment
    language vs. pure-research language.

    IMPORTANT: only descriptions attached to a Tier S/A title are trusted as signal here.
    Exploration showed descriptions are randomly shuffled relative to title ~84% of the
    time for non-technical titles, so scanning ALL descriptions regardless of title would
    let an HR Manager's randomly-assigned "shipped to production" description (meant for
    a different candidate's tech role) count as a positive signal. We only read
    descriptions from roles whose own title already indicates plausible relevance.
    """
    relevant_text = " ".join(
        ch.get("description", "").lower()
        for ch in career_history
        if title_tier(ch["title"]) in {"direct", "adjacent"}
    )
    if not relevant_text:
        return 0.0
    prod_hits = sum(1 for phrase in PRODUCTION_SIGNAL_PHRASES if phrase in relevant_text)
    research_hits = sum(1 for phrase in RESEARCH_ONLY_SIGNAL_PHRASES if phrase in relevant_text)
    score = min(1.0, 0.25 * prod_hits)
    if research_hits > 0 and prod_hits == 0:
        score = max(0.0, score - 0.3)
    return score


def title_relevance_gate(current_title: str, career_history: list) -> float:
    """
    The dominant gating signal. Returns a multiplier in (0, 1].

    Built after discovering (see notebooks/explore3.py) that career_history
    description text is topic-matched to the role's title ~100% of the time
    for ML/AI titles, but only ~16% of the time for common non-tech titles
    (the other 84% are randomly shuffled descriptions from an unrelated
    pool). That means description content can't be trusted to GRANT
    relevance on its own -- only title can. This directly defends against
    the JD's explicitly-stated trap: a non-technical title padded with
    AI-flavored skills/summary text must not outrank someone whose actual
    job has been doing this work.

    Logic:
      - current title in Tier S (direct ML/AI/search role) -> 1.0
      - current title in Tier A (adjacent data/software role) -> 0.6,
        bumped to 0.8 if ANY prior role was Tier S (real transition story,
        e.g. the data engineer moving into ML)
      - current title in Tier B (generic dev role) -> 0.35, bumped to 0.6
        if a prior role was Tier S
      - current title in Tier D (no technical connection at all) -> 0.05,
        bumped only modestly (0.25) even with a Tier S prior role, since a
        regression FROM an ML role INTO e.g. HR Manager is itself a strong
        signal this person is no longer doing this work and is much less
        believable as a transition story than the reverse direction.
    """
    cur_tier = title_tier(current_title)
    history_tiers = {title_tier(ch["title"]) for ch in career_history}
    had_direct_history = "direct" in history_tiers

    if cur_tier == "direct":
        return 1.0
    if cur_tier == "adjacent":
        return 0.8 if had_direct_history else 0.6
    if cur_tier == "weak":
        return 0.6 if had_direct_history else 0.35
    if cur_tier == "none":
        return 0.25 if had_direct_history else 0.05
    return 0.3  # unknown title, shouldn't happen given closed vocabulary


def skill_profile_features(skills: list, assessment_scores: dict) -> dict:
    """
    Aggregate the candidate's skill list into taxonomy-bucketed counts, weighted by
    *verified* assessment score where available (trust platform-tested skill over
    self-reported proficiency -- this is the system's main defense against keyword stuffing).
    """
    prof_weight = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}
    core_score = 0.0
    adjacent_score = 0.0
    cv_speech_count = 0
    irrelevant_count = 0
    total = len(skills) if skills else 1
    self_report_assessment_gap = []

    for s in skills:
        name = s["name"]
        cat = skill_category(name)
        self_w = prof_weight.get(s.get("proficiency"), 0.4)
        verified = assessment_scores.get(name)
        if verified is not None:
            verified_w = verified / 100.0
            # trust the verified score more than self-report; blend 70/30 toward verified
            eff_w = 0.7 * verified_w + 0.3 * self_w
            gap = self_w - verified_w
            if gap > 0.35:
                self_report_assessment_gap.append(name)
        else:
            eff_w = self_w * 0.85  # slight discount for unverifiable self-report

        if cat == "core":
            core_score += eff_w
        elif cat == "adjacent":
            adjacent_score += eff_w
        elif cat == "cv_speech":
            cv_speech_count += 1
        elif cat == "irrelevant":
            irrelevant_count += 1

    return {
        "core_skill_score": core_score,
        "adjacent_skill_score": adjacent_score,
        "cv_speech_fraction": cv_speech_count / total,
        "irrelevant_fraction": irrelevant_count / total,
        "inflated_skill_count": len(self_report_assessment_gap),
    }


def cv_speech_only_penalty(cv_speech_fraction: float, core_skill_score: float) -> float:
    """JD: CV/speech/robotics ONLY (without NLP/IR) is explicitly not a fit."""
    if cv_speech_fraction > 0.3 and core_skill_score < 1.0:
        return 0.5
    return 1.0


def honeypot_sanity_flag(candidate: dict) -> bool:
    """
    Two clean, low-noise impossible-profile signals found via data exploration:
      1. >=1 skill marked 'expert' proficiency with 0 duration_months (can't be
         an expert in something you've used for zero time).
      2. years_of_experience vastly mismatched (>3yrs off) from the sum of
         career_history duration_months (timeline doesn't add up).
    Candidates tripping either flag are forced to the bottom of the ranking.
    """
    skills = candidate.get("skills", [])
    expert_zero = any(
        s.get("proficiency") == "expert" and s.get("duration_months", 1) == 0
        for s in skills
    )
    if expert_zero:
        return True

    yoe = candidate["profile"]["years_of_experience"]
    total_months = sum(ch.get("duration_months", 0) for ch in candidate.get("career_history", []))
    if abs(yoe - total_months / 12.0) > 3:
        return True

    return False


def recency_score(last_active_date: str) -> float:
    months = _months_since(last_active_date)
    if months <= 1:
        return 1.0
    if months <= 3:
        return 0.8
    if months <= 6:
        return 0.55
    if months <= 9:
        return 0.3
    return 0.1


def availability_score(sig: dict) -> float:
    """
    JD's explicit instruction: 'a perfect-on-paper candidate who hasn't logged in for
    6 months and has a 5% recruiter response rate is, for hiring purposes, not actually
    available. Down-weight them appropriately.'
    """
    rec = recency_score(sig["last_active_date"])
    resp = sig["recruiter_response_rate"]
    open_flag = 1.0 if sig["open_to_work_flag"] else 0.5  # not disqualifying, JD wants top talent even if passive
    interview_rate = sig.get("interview_completion_rate", 0.5)
    # weighted blend
    return 0.35 * rec + 0.30 * resp + 0.20 * open_flag + 0.15 * interview_rate


def extract_features(candidate: dict) -> dict:
    """Main entry point: compute all structured features for one candidate record."""
    p = candidate["profile"]
    sig = candidate["redrob_signals"]
    history = candidate["career_history"]

    skill_feats = skill_profile_features(candidate.get("skills", []), sig.get("skill_assessment_scores", {}))

    feats = {
        "candidate_id": candidate["candidate_id"],
        "experience_fit": experience_fit_score(p["years_of_experience"]),
        "location_fit": location_fit_score(p["country"], p["location"], sig["willing_to_relocate"]),
        "notice_fit": notice_period_score(sig["notice_period_days"]),
        "title_relevance_gate": title_relevance_gate(p["current_title"], history),
        "consulting_penalty": consulting_only_penalty(history, p["current_industry"], p["current_company"]),
        "architecture_penalty": architecture_only_penalty(p["current_title"], history),
        "title_chaser_penalty": title_chaser_penalty(history),
        "production_signal": production_signal_score(history),
        "cv_speech_penalty": cv_speech_only_penalty(skill_feats["cv_speech_fraction"], skill_feats["core_skill_score"]),
        "availability": availability_score(sig),
        "is_honeypot": honeypot_sanity_flag(candidate),
        **skill_feats,
    }
    return feats

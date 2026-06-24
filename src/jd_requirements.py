"""
Structured representation of the Redrob "Senior AI Engineer - Founding Team" JD.

This was built by manually reading job_description.docx in full and extracting
the requirements, disqualifiers, and "ideal candidate" signals the JD describes.
We do this once, by hand/carefully, rather than building an automated JD parser,
because there is exactly one JD for this challenge -- automating the parse of a
single document would add complexity without adding value. A production version
of this system would replace this file with an LLM-based JD parser (see writeup).
"""

# --- Experience band -------------------------------------------------------
# JD: "5-9 years... not a hard requirement... ideal candidate is 6-8 years
# total, of which 4-5 are applied ML/AI at product companies."
EXPERIENCE_MIN_SOFT = 5
EXPERIENCE_MAX_SOFT = 9
EXPERIENCE_IDEAL_MIN = 6
EXPERIENCE_IDEAL_MAX = 8
EXPERIENCE_HARD_FLOOR = 2   # below this, JD's "5-9 yrs, flexible" framing no longer plausibly applies

# --- Location ---------------------------------------------------------------
# JD: "Pune/Noida preferred... Hyderabad, Pune, Mumbai, Delhi NCR welcome...
# Outside India: case-by-case, no visa sponsorship."
LOCATION_TIER_A = {"Pune, Maharashtra", "Noida, Uttar Pradesh"}
LOCATION_TIER_B = {"Hyderabad, Telangana", "Mumbai, Maharashtra", "Delhi, Delhi", "Gurgaon, Haryana"}
# Remaining India cities: Tier C (same country, not named, but relocation-plausible)
COUNTRY_INDIA = "India"

# --- Notice period -----------------------------------------------------------
# JD: "We'd love sub-30-day notice. We can buy out up to 30 days.
# 30+ day notice candidates still in scope but the bar gets higher."
NOTICE_IDEAL_MAX_DAYS = 30
NOTICE_ACCEPTABLE_MAX_DAYS = 60  # beyond this, meaningfully tougher bar

# --- Disqualifiers (career-history / title pattern based) -------------------
# JD section "Things we explicitly do NOT want" + the hard disqualifiers under
# "what we mean by 5-9 years."
CONSULTING_FIRMS = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
                     "tata consultancy", "hcl", "tech mahindra"}

# Titles that signal "tech lead / architecture, not writing code" per JD's
# explicit disqualifier ("hasn't written production code in 18 months").
NON_CODING_SENIOR_TITLES = {"engineering manager", "director", "vp engineering",
                             "head of engineering", "cto"}

# Title-chaser pattern: JD calls out switching companies ~every 1.5 years while
# climbing a title ladder (Senior -> Staff -> Principal) as a red flag.
TITLE_LADDER_WORDS = ["senior", "staff", "principal", "lead"]

# --- Core production-system signal phrases ----------------------------------
# JD: "the right answer involves reasoning about... built a recommendation
# system at a product company." We scan career_history descriptions for
# evidence of *shipping* something, not just knowing about it.
PRODUCTION_SIGNAL_PHRASES = [
    "production", "deployed", "shipped", "scale", "real users", "real-time",
    "live system", "serving", "latency", "throughput", "rolled out",
]

RESEARCH_ONLY_SIGNAL_PHRASES = [
    "academic", "research lab", "published paper", "thesis", "phd research",
]

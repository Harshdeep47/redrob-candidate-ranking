const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Harshdeep Singh";
pres.title = "Redrob Candidate Ranking -- Methodology";

const W = 13.3, H = 7.5;

// Palette: Charcoal Minimal + teal accent (engineering/data-systems feel)
const INK = "1A2230";        // near-black navy-charcoal, primary text/bg
const SLATE = "3C4A5E";      // secondary
const PAPER = "F4F6F8";      // light bg
const TEAL = "1E9C8B";       // accent
const TEAL_DARK = "12685D";
const WARN = "C8553D";       // muted terracotta for "problem/bug" moments
const MUTE = "8B97A5";       // muted gray text on dark
const WHITE = "FFFFFF";

function darkSlide() {
  let s = pres.addSlide();
  s.background = { color: INK };
  return s;
}
function lightSlide() {
  let s = pres.addSlide();
  s.background = { color: PAPER };
  return s;
}

function kicker(s, text, color = TEAL) {
  s.addText(text.toUpperCase(), {
    x: 0.6, y: 0.45, w: 8, h: 0.35,
    fontSize: 12, color, bold: true, charSpacing: 2, fontFace: "Calibri",
  });
}
function title(s, text, opts = {}) {
  s.addText(text, {
    x: 0.6, y: opts.y ?? 0.78, w: opts.w ?? 11.8, h: opts.h ?? 0.9,
    fontSize: opts.fontSize ?? 30, color: opts.color ?? INK, bold: true,
    fontFace: "Cambria", margin: 0,
  });
}
function pageNum(s, n) {
  s.addText(String(n), {
    x: W - 0.7, y: H - 0.45, w: 0.4, h: 0.3,
    fontSize: 10, color: MUTE, align: "right", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 1 -- TITLE
// ============================================================
{
  let s = darkSlide();
  s.addText("REDROB · INTELLIGENT CANDIDATE DISCOVERY & RANKING CHALLENGE", {
    x: 0.8, y: 2.1, w: 11.7, h: 0.4,
    fontSize: 13, color: TEAL, bold: true, charSpacing: 2, fontFace: "Calibri",
  });
  s.addText("Ranking 100,000 candidates\nthe way a recruiter actually reads a resume", {
    x: 0.8, y: 2.6, w: 11.7, h: 2.2,
    fontSize: 38, color: WHITE, bold: true, fontFace: "Cambria", lineSpacing: 44,
  });
  s.addText(
    "A title-gated hybrid ranker built CPU-only, no GPU, no network calls --\nand the data-driven discovery that shaped its central design decision.",
    { x: 0.8, y: 4.75, w: 10.5, h: 0.9, fontSize: 15, color: MUTE, fontFace: "Calibri", lineSpacing: 22 }
  );
  s.addShape(pres.shapes.OVAL, { x: 10.6, y: 0.6, w: 2.0, h: 2.0, fill: { color: TEAL, transparency: 88 }, line: { type: "none" } });
  s.addShape(pres.shapes.OVAL, { x: 11.6, y: 5.4, w: 1.3, h: 1.3, fill: { color: TEAL, transparency: 85 }, line: { type: "none" } });
  s.addText("Harshdeep Singh", {
    x: 0.8, y: 6.6, w: 6, h: 0.4, fontSize: 13, color: WHITE, bold: true, fontFace: "Calibri",
  });
  s.addText("github.com/Harshdeep47", {
    x: 0.8, y: 6.95, w: 6, h: 0.35, fontSize: 11, color: MUTE, fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 2 -- THE PROBLEM, RESTATED
// ============================================================
{
  let s = lightSlide();
  kicker(s, "01 -- The brief");
  title(s, "Rank 100K candidates the way a great\nrecruiter would -- not by keyword match", { fontSize: 27, h: 1.3 });

  const cards = [
    { h: "Read the JD", b: "Understand what the role actually needs, not just extract words from it.", icon: "\uD83D\uDCC4" },
    { h: "Read the whole profile", b: "Career history, skills, behavioral signals, platform activity -- the full picture.", icon: "\uD83D\uDD0E" },
    { h: "Defend the shortlist", b: "Deliver a ranked list a recruiter could actually trust and act on.", icon: "\u2705" },
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.13;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 2.3, w: 3.85, h: 3.0, rectRadius: 0.08,
      fill: { color: WHITE }, line: { color: "DDE3E8", width: 1 },
      shadow: { type: "outer", color: "000000", blur: 8, offset: 3, angle: 90, opacity: 0.08 },
    });
    s.addText(c.icon, { x: x + 0.3, y: 2.55, w: 0.9, h: 0.7, fontSize: 28 });
    s.addText(c.h, { x: x + 0.3, y: 3.25, w: 3.25, h: 0.5, fontSize: 17, bold: true, color: INK, fontFace: "Cambria" });
    s.addText(c.b, { x: x + 0.3, y: 3.78, w: 3.25, h: 1.3, fontSize: 12.5, color: SLATE, fontFace: "Calibri", lineSpacing: 17 });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 5.7, w: 12.1, h: 1.15, rectRadius: 0.08,
    fill: { color: INK }, line: { type: "none" },
  });
  s.addText([
    { text: "The trap the brief names explicitly: ", options: { bold: true, color: TEAL } },
    { text: "\u201Ca candidate who has all the AI keywords listed as skills but whose title is \u2018Marketing Manager\u2019 is not a fit, no matter how perfect their skill list looks.\u201D", options: { italic: true, color: WHITE } },
  ], { x: 0.95, y: 5.85, w: 11.4, h: 0.9, fontSize: 13.5, fontFace: "Calibri", valign: "middle", lineSpacing: 18 });

  pageNum(s, 2);
}

// ============================================================
// SLIDE 3 -- WHAT THE DATA ACTUALLY LOOKS LIKE
// ============================================================
{
  let s = lightSlide();
  kicker(s, "02 -- Exploration, not assumption");
  title(s, "Before writing a scorer, I read the data", { fontSize: 27 });

  const stats = [
    ["100,000", "candidate profiles, 1 fixed JD"],
    ["75%", "based in India; rest spread across 7 countries"],
    ["133", "distinct skill names -- a closed vocabulary"],
    ["48", "distinct job titles -- also closed"],
  ];
  stats.forEach((st, i) => {
    const x = 0.6 + i * 3.1;
    s.addText(st[0], { x, y: 2.25, w: 2.9, h: 0.85, fontSize: 34, bold: true, color: TEAL_DARK, fontFace: "Cambria", align: "left" });
    s.addText(st[1], { x, y: 3.05, w: 2.85, h: 0.8, fontSize: 12.5, color: SLATE, fontFace: "Calibri", lineSpacing: 16 });
  });
  s.addShape(pres.shapes.LINE, { x: 0.6, y: 4.05, w: 12.1, h: 0, line: { color: "DDE3E8", width: 1 } });

  s.addText("Two adversarial patterns surfaced immediately:", {
    x: 0.6, y: 4.3, w: 11, h: 0.4, fontSize: 15, bold: true, color: INK, fontFace: "Cambria",
  });

  const findings = [
    { n: "~5,500", t: "candidates", d: "non-technical titles (HR Manager, Sales Executive...) paired with templated \u201CAI enthusiast\u201D summary language -- the brief's keyword-stuffing trap, at scale." },
    { n: "68", t: "honeypots", d: "impossible profiles: \u201Cexpert\u201D skill with 0 months' use, or years-of-experience that doesn't add up against career history." },
  ];
  findings.forEach((f, i) => {
    const x = 0.6 + i * 6.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 4.85, w: 5.85, h: 1.85, rectRadius: 0.08,
      fill: { color: WHITE }, line: { color: "DDE3E8", width: 1 },
      shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.06 },
    });
    s.addText([
      { text: f.n + " ", options: { bold: true, color: WARN, fontSize: 22 } },
      { text: f.t, options: { color: SLATE, fontSize: 13 } },
    ], { x: x + 0.3, y: 5.0, w: 5.3, h: 0.45, fontFace: "Calibri" });
    s.addText(f.d, { x: x + 0.3, y: 5.5, w: 5.3, h: 1.1, fontSize: 12, color: SLATE, fontFace: "Calibri", lineSpacing: 15 });
  });

  pageNum(s, 3);
}

// ============================================================
// SLIDE 4 -- THE CENTRAL DISCOVERY
// ============================================================
{
  let s = darkSlide();
  kicker(s, "03 -- The discovery that shaped everything", TEAL);
  s.addText("Titles are trustworthy. Free text isn't\n-- not equally, anyway.", {
    x: 0.6, y: 0.95, w: 12, h: 1.3, fontSize: 27, bold: true, color: WHITE, fontFace: "Cambria", lineSpacing: 32,
  });

  s.addText(
    "I checked whether each career_history entry's description actually matches its own title topically.",
    { x: 0.6, y: 2.35, w: 11.8, h: 0.5, fontSize: 14, color: MUTE, fontFace: "Calibri" }
  );

  // two big comparison bars
  const barY = 3.1, barH = 1.7, barW = 5.6;
  // ML titles
  s.addText("ML / AI titles", { x: 0.6, y: barY - 0.05, w: 3, h: 0.4, fontSize: 14, bold: true, color: TEAL, fontFace: "Calibri" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: barY + 0.45, w: barW, h: 0.55, rectRadius: 0.05, fill: { color: "2A3445" }, line: { type: "none" } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: barY + 0.45, w: barW, h: 0.55, rectRadius: 0.05, fill: { color: TEAL }, line: { type: "none" } });
  s.addText("100%", { x: 0.6, y: barY + 0.45, w: barW, h: 0.55, fontSize: 20, bold: true, color: INK, align: "center", valign: "middle", fontFace: "Cambria" });
  s.addText("description content matches the role's own title", { x: 0.6, y: barY + 1.1, w: barW, h: 0.5, fontSize: 11.5, color: MUTE, fontFace: "Calibri" });

  // non-tech titles
  const x2 = 7.0;
  s.addText("Non-technical titles", { x: x2, y: barY - 0.05, w: 3, h: 0.4, fontSize: 14, bold: true, color: WARN, fontFace: "Calibri" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x2, y: barY + 0.45, w: barW, h: 0.55, rectRadius: 0.05, fill: { color: "2A3445" }, line: { type: "none" } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x2, y: barY + 0.45, w: barW * 0.16, h: 0.55, rectRadius: 0.05, fill: { color: WARN }, line: { type: "none" } });
  s.addText("16%", { x: x2, y: barY + 0.45, w: barW * 0.16 + 0.6, h: 0.55, fontSize: 20, bold: true, color: WHITE, align: "right", valign: "middle", fontFace: "Cambria" });
  s.addText("match rate -- the other 84% are shuffled in from an unrelated pool", { x: x2, y: barY + 1.1, w: barW, h: 0.5, fontSize: 11.5, color: MUTE, fontFace: "Calibri" });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 5.7, w: 12.1, h: 1.25, rectRadius: 0.08, fill: { color: "212B3A" }, line: { type: "none" },
  });
  s.addText([
    { text: "Conclusion: ", options: { bold: true, color: TEAL } },
    { text: "title has to be the dominant, trustworthy signal for relevance. Free text (description, summary, self-reported skills) can confirm depth once relevance is established by title -- it cannot grant relevance on its own.", options: { color: WHITE } },
  ], { x: 0.95, y: 5.85, w: 11.4, h: 0.95, fontSize: 13.5, fontFace: "Calibri", valign: "middle", lineSpacing: 17 });

  pageNum(s, 4);
}

// ============================================================
// SLIDE 5 -- THE BUG STORY (found in real QA)
// ============================================================
{
  let s = lightSlide();
  kicker(s, "04 -- Found the hard way", WARN);
  title(s, "v1 of the pipeline put an HR Manager\nin the top 100. Here's why.", { fontSize: 26, h: 1.3 });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 2.25, w: 12.1, h: 1.7, rectRadius: 0.08,
    fill: { color: "FBEFEC" }, line: { color: WARN, width: 1.25 },
  });
  s.addText("CAND_0059448  --  rank #100, v1 output", {
    x: 0.95, y: 2.4, w: 11.4, h: 0.35, fontSize: 12, bold: true, color: WARN, fontFace: "Calibri",
  });
  s.addText(
    '"HR Manager at Wipro... directly relevant skills: Recommendation Systems (advanced), Sentence Transformers (advanced), FAISS (intermediate)"',
    { x: 0.95, y: 2.78, w: 11.4, h: 0.6, fontSize: 13, italic: true, color: INK, fontFace: "Calibri" }
  );
  s.addText(
    "Self-reported skills looked great. Career history (HR, then Content Writing) had nothing to do with ML/AI/search. v1 had no mechanism to weigh that.",
    { x: 0.95, y: 3.4, w: 11.4, h: 0.5, fontSize: 12, color: SLATE, fontFace: "Calibri" }
  );

  // before/after fix
  const fy = 4.2;
  s.addText("THE FIX", { x: 0.6, y: fy, w: 4, h: 0.35, fontSize: 13, bold: true, color: TEAL_DARK, charSpacing: 2, fontFace: "Calibri" });

  const steps = [
    ["1", "title_relevance_gate()", "Multiplicative gate over a closed taxonomy of all 48 titles: direct / adjacent / weak / none."],
    ["2", "Title-gated production_signal_score()", "Only trust career-history descriptions attached to a plausibly-relevant title."],
    ["3", "Title-gated reasoning quotes", "Never present a shuffled, untrustworthy description as evidence in the output."],
  ];
  steps.forEach((st, i) => {
    const x = 0.6 + i * 4.13;
    s.addShape(pres.shapes.OVAL, { x, y: fy + 0.5, w: 0.5, h: 0.5, fill: { color: TEAL }, line: { type: "none" } });
    s.addText(st[0], { x, y: fy + 0.5, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Cambria" });
    s.addText(st[1], { x: x + 0.65, y: fy + 0.45, w: 3.3, h: 0.55, fontSize: 12.5, bold: true, color: INK, fontFace: "Calibri" });
    s.addText(st[2], { x, y: fy + 1.05, w: 3.85, h: 1.1, fontSize: 11, color: SLATE, fontFace: "Calibri", lineSpacing: 14 });
  });

  pageNum(s, 5);
}

// ============================================================
// SLIDE 6 -- ARCHITECTURE
// ============================================================
{
  let s = darkSlide();
  kicker(s, "05 -- Architecture");
  s.addText("Two stages: precompute once, rank in seconds", {
    x: 0.6, y: 0.85, w: 12, h: 0.7, fontSize: 27, bold: true, color: WHITE, fontFace: "Cambria",
  });

  // pipeline flow
  const py = 2.0;
  const boxes = [
    { t: "candidates.jsonl", sub: "100,000 records", w: 2.0 },
    { t: "precompute.py", sub: "features + TF-IDF\n~45-80s, not time-boxed", w: 2.6 },
    { t: "artifacts/", sub: "parquet + npz\ncached to disk", w: 1.9 },
    { t: "rank.py", sub: "hybrid score + gates\n~4-5s, the deliverable", w: 2.6 },
    { t: "submission.csv", sub: "top 100, ranked", w: 2.0 },
  ];
  let x = 0.5;
  const gap = 0.35;
  boxes.forEach((b, i) => {
    const fillC = (i === 1 || i === 3) ? TEAL : "2A3445";
    const textC = (i === 1 || i === 3) ? INK : WHITE;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: py, w: b.w, h: 1.3, rectRadius: 0.08, fill: { color: fillC }, line: { type: "none" } });
    s.addText(b.t, { x, y: py + 0.15, w: b.w, h: 0.4, fontSize: 12.5, bold: true, color: textC, align: "center", fontFace: "Calibri" });
    s.addText(b.sub, { x: x + 0.05, y: py + 0.55, w: b.w - 0.1, h: 0.7, fontSize: 9.5, color: textC, align: "center", fontFace: "Calibri", lineSpacing: 12 });
    if (i < boxes.length - 1) {
      s.addText("\u2192", { x: x + b.w, y: py + 0.35, w: gap, h: 0.6, fontSize: 20, color: MUTE, align: "center", valign: "middle" });
    }
    x += b.w + gap;
  });

  s.addText("Why this split matters:", { x: 0.6, y: 3.9, w: 5, h: 0.4, fontSize: 14, bold: true, color: TEAL, fontFace: "Calibri" });
  s.addText(
    "The spec time-boxes ranking to \u22645 min / \u226416GB / CPU-only / no network -- but not the work needed to get there. Splitting lets the expensive one-time cost (TF-IDF fit over 100K docs) sit outside the budget entirely, while the actual graded step stays a few seconds even at full scale.",
    { x: 0.6, y: 4.35, w: 6.0, h: 2.4, fontSize: 12.5, color: MUTE, fontFace: "Calibri", lineSpacing: 18 }
  );

  s.addText("Why TF-IDF, not a neural embedding model:", { x: 6.95, y: 3.9, w: 5.7, h: 0.4, fontSize: 14, bold: true, color: TEAL, fontFace: "Calibri" });
  s.addText(
    "Tried sentence-transformers first. It pulls a multi-GB CUDA/PyTorch stack even for CPU-only inference -- exactly the dependency bloat that risks breaking a clean Docker rebuild. The vocabulary here is narrow and mostly closed (133 skills, 48 titles, one JD), so TF-IDF + cosine similarity does the job with zero exotic dependencies and fully auditable scores.",
    { x: 6.95, y: 4.35, w: 5.7, h: 2.6, fontSize: 12.5, color: MUTE, fontFace: "Calibri", lineSpacing: 18 }
  );

  pageNum(s, 6);
}

// ============================================================
// SLIDE 7 -- THE SCORING FORMULA
// ============================================================
{
  let s = lightSlide();
  kicker(s, "06 -- The hybrid score");
  title(s, "Additive for fit, multiplicative for disqualifiers", { fontSize: 26 });

  s.addText("BASE SCORE  (weighted sum, 0\u20131)", { x: 0.6, y: 1.95, w: 6, h: 0.35, fontSize: 12, bold: true, color: TEAL_DARK, charSpacing: 1, fontFace: "Calibri" });
  const weights = [
    ["0.28", "Semantic similarity", "TF-IDF cosine vs. JD"],
    ["0.22", "Core skill score", "verified assessment > self-report"],
    ["0.16", "Production signal", "shipped-to-prod language, title-gated"],
    ["0.12", "Availability", "recency, response rate, open-to-work"],
    ["0.10", "Experience fit", "JD's 6\u20138yr ideal band"],
    ["0.07", "Location fit", "Pune/Noida > other India > abroad"],
    ["0.05", "Notice period fit", "sub-30-day preferred"],
  ];
  let wy = 2.35;
  weights.forEach((w) => {
    s.addText(w[0], { x: 0.6, y: wy, w: 0.7, h: 0.36, fontSize: 14, bold: true, color: TEAL_DARK, fontFace: "Cambria" });
    s.addText(w[1], { x: 1.4, y: wy, w: 2.7, h: 0.36, fontSize: 12.5, bold: true, color: INK, fontFace: "Calibri" });
    s.addText(w[2], { x: 4.15, y: wy, w: 2.4, h: 0.36, fontSize: 10.5, color: SLATE, fontFace: "Calibri" });
    wy += 0.46;
  });

  s.addShape(pres.shapes.LINE, { x: 6.85, y: 1.95, w: 0, h: 4.9, line: { color: "DDE3E8", width: 1 } });

  s.addText("MULTIPLICATIVE GATES  (0\u20131, applied after)", { x: 7.15, y: 1.95, w: 5.5, h: 0.35, fontSize: 12, bold: true, color: WARN, charSpacing: 1, fontFace: "Calibri" });
  const gates = [
    ["title_relevance_gate", "0.05-1.0", "the dominant gate -- see slide 4/5"],
    ["visa_gate_penalty", "0.15", "non-India + not willing to relocate"],
    ["consulting_only_penalty", "0.35", "ALL career history at consulting firms"],
    ["cv_speech_only_penalty", "0.5", "CV/speech-heavy, no NLP/IR depth"],
    ["architecture_only_penalty", "0.5", "senior, hasn't coded in 18+ months"],
    ["title_chaser_penalty", "0.6", "ladder-climbing via company-hopping"],
    ["honeypot suppression", "0.01", "impossible-profile sanity flags"],
  ];
  let gy = 2.35;
  gates.forEach((g) => {
    s.addText(g[0], { x: 7.15, y: gy, w: 3.3, h: 0.34, fontSize: 11.5, bold: true, color: INK, fontFace: "Calibri" });
    s.addText(g[1], { x: 10.5, y: gy, w: 1.05, h: 0.34, fontSize: 12, bold: true, color: WARN, align: "right", fontFace: "Cambria" });
    s.addText(g[2], { x: 7.15, y: gy + 0.32, w: 5.3, h: 0.3, fontSize: 9.5, italic: true, color: MUTE, fontFace: "Calibri" });
    gy += 0.69;
  });

  pageNum(s, 7);
}

// ============================================================
// SLIDE 8 -- RESULTS / VALIDATION
// ============================================================
{
  let s = darkSlide();
  kicker(s, "07 -- Validation");
  s.addText("What the final output actually looks like", {
    x: 0.6, y: 0.85, w: 12, h: 0.7, fontSize: 27, bold: true, color: WHITE, fontFace: "Cambria",
  });

  const checks = [
    ["100% Tier-S titles", "every top-100 candidate currently holds a direct ML/AI/search role"],
    ["0 honeypots", "in the top 100 (68 found across the full pool, all suppressed)"],
    ["0 keyword decoys", "the ~5,500-candidate aspirational-AI trap, fully filtered"],
    ["97 / 100 India-based", "3 non-India, all confirmed willing to relocate"],
    ["~4 sec runtime", "full 100K pool, cached artifacts, <1GB RAM"],
    ["Deterministic", "byte-identical output across repeated runs"],
  ];
  let cx = 0.6, cy = 2.0;
  checks.forEach((c, i) => {
    if (i === 3) { cx = 0.6; cy = 4.5; }
    const w = 3.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cy, w, h: 2.1, rectRadius: 0.08, fill: { color: "212B3A" }, line: { type: "none" } });
    s.addShape(pres.shapes.OVAL, { x: cx + 0.3, y: cy + 0.3, w: 0.45, h: 0.45, fill: { color: TEAL }, line: { type: "none" } });
    s.addText("\u2713", { x: cx + 0.3, y: cy + 0.3, w: 0.45, h: 0.45, fontSize: 18, bold: true, color: INK, align: "center", valign: "middle" });
    s.addText(c[0], { x: cx + 0.3, y: cy + 0.9, w: w - 0.6, h: 0.45, fontSize: 15, bold: true, color: WHITE, fontFace: "Cambria" });
    s.addText(c[1], { x: cx + 0.3, y: cy + 1.35, w: w - 0.6, h: 0.65, fontSize: 10.5, color: MUTE, fontFace: "Calibri", lineSpacing: 13 });
    cx += w + 0.2;
  });

  pageNum(s, 8);
}

// ============================================================
// SLIDE 9 -- LIMITATIONS / NEXT STEPS
// ============================================================
{
  let s = lightSlide();
  kicker(s, "08 -- Honest limitations", WARN);
  title(s, "What I'd change with more time", { fontSize: 27 });

  const items = [
    ["JD parsing is manual", "Only one JD exists for this challenge, so I read it by hand. A real product needs an automated parser so the system generalizes without a code change."],
    ["TF-IDF won't generalize", "Works well for this single, narrow-vocabulary JD. A real product would want a cached neural embedding step (still no GPU at rank time) with TF-IDF as a fallback."],
    ["Reasoning is templated, not LLM-polished", "Deliberate, to guarantee zero hallucination under a no-network rank step. An offline, precompute-time LLM pass could improve phrasing without that risk."],
    ["Weights are reasoned, not learned", "No ground truth was available to fit against. With labeled outcomes this becomes a learned ranker (logistic regression / GBM) over the same feature set."],
  ];
  let iy = 2.2;
  items.forEach((it) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: iy, w: 12.1, h: 1.05, rectRadius: 0.06, fill: { color: WHITE }, line: { color: "DDE3E8", width: 1 } });
    s.addText(it[0], { x: 0.9, y: iy + 0.12, w: 3.5, h: 0.8, fontSize: 13.5, bold: true, color: INK, fontFace: "Cambria", valign: "middle" });
    s.addText(it[1], { x: 4.6, y: iy + 0.12, w: 7.9, h: 0.8, fontSize: 11.5, color: SLATE, fontFace: "Calibri", valign: "middle", lineSpacing: 14 });
    iy += 1.2;
  });

  pageNum(s, 9);
}

// ============================================================
// SLIDE 10 -- CLOSE
// ============================================================
{
  let s = darkSlide();
  s.addShape(pres.shapes.OVAL, { x: -1.5, y: -1.5, w: 4, h: 4, fill: { color: TEAL, transparency: 90 }, line: { type: "none" } });
  s.addText("Built, broken, and fixed in public --\nsee the git history.", {
    x: 0.8, y: 2.6, w: 11.5, h: 1.6, fontSize: 32, bold: true, color: WHITE, fontFace: "Cambria", lineSpacing: 38,
  });
  s.addText(
    "Every architectural decision in this deck traces back to a specific exploration finding or a specific bug found in real output -- not a guess. The commit history shows the v1 bug, the root-cause investigation, and the fix, in that order.",
    { x: 0.8, y: 4.3, w: 9.5, h: 1.1, fontSize: 14, color: MUTE, fontFace: "Calibri", lineSpacing: 19 }
  );
  s.addText("github.com/Harshdeep47/redrob-candidate-ranking", {
    x: 0.8, y: 6.5, w: 8, h: 0.4, fontSize: 13, color: TEAL, bold: true, fontFace: "Calibri",
  });
}

pres.writeFile({ fileName: "/home/claude/redrob-hackathon/methodology_deck/methodology.pptx" })
  .then(() => console.log("done"));

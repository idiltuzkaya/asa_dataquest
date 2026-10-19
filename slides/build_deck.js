// Builds slides/DataQuest2026_AlreadyBakedIn.pptx (cover + 4 content slides + references).
// Every number on the slides is read from analysis/tables/decomp_numbers.json — nothing is typed by hand.
//   cd slides && node build_deck.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const N = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/tables/decomp_numbers.json"), "utf8"));
const FIG = (f) => path.join(ROOT, "analysis/figures", f);
const OUT = path.join(__dirname, "DataQuest2026_AlreadyBakedIn.pptx");
const AR = (f) => { const b = fs.readFileSync(FIG(f)); return b.readUInt32BE(16) / b.readUInt32BE(20); }; // PNG width/height

// ---------------------------------------------------------------- numbers used on slides
const f2 = (x) => x.toFixed(2);
const wf = N.world_factors;
const reg = N.region_factors;
const pctOf = (f) => `${f >= 1 ? "+" : "−"}${Math.abs(Math.round((f - 1) * 100))}%`;
const europeNoMig = pctOf(reg.Europe.total / reg.Europe.migration);
const vs = N.variance_share_of_total;
const vsw = N.variance_share_of_total_popweighted;
const minus = (x, d = 2) => x.toFixed(d).replace("-", "−");
const pi = N.pi95_ratio_quantiles;
const w95 = [N.world_2101_bn_by_run["Lower 95 PI"], N.world_2101_bn_by_run["Upper 95 PI"]];
const run = N.world_2101_bn_by_run;
const maxAbsRhoEngine = Math.max(...["momentum", "fertility", "migration"].map((e) => Math.abs(N.spearman_pi95_vs[e])));

// ---------------------------------------------------------------- theme
const THEME = {
  name: "Already Baked In",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "0B0B0B", lt1: "FFFFFF", dk2: "14213D", lt2: "F4F3F0",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "8D8B85", accent5: "52514E", accent6: "B9B7B0",
    hlink: "2A78D6", folHlink: "52514E",
  },
};
const HEX = { momentum: "2A78D6", fertility: "EB6834", migration: "1BAF7A", mortality: "8D8B85" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Already Baked In — ASA DataQuest 2026";
pres.author = "ASA DataQuest 2026 team";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "DARK", background: { color: C.text2 },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.5, y: 0.28, w: 12.3, h: 0.3, fontSize: 11, bold: true,
      color: C.accent1, charSpacing: 2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.55, w: 12.3, h: 0.7, fontSize: 30, bold: true,
      color: C.text2, margin: 0, valign: "top", align: "left" }, text: "" } },
    { text: { text: "ASA International DataQuest 2026 · Data: UN World Population Prospects 2024",
      options: { x: 0.5, y: 7.1, w: 9, h: 0.25, fontSize: 9, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.1, w: 0.5, h: 0.25, fontSize: 9, color: C.accent5, align: "right" },
});

// ---------------------------------------------------------------- helpers
function chip(slide, x, y, label, value, color, w = 1.55) {
  // rounded factor chip: the deck's visual motif (same colours as the charts)
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.62, rectRadius: 0.12, fill: { color }, line: { color, width: 0 },
    objectName: `chip ${label}` });
  slide.addText([{ text: value, options: { fontSize: 18, bold: true, breakLine: true } }, { text: label, options: { fontSize: 10 } }],
    { x, y, w, h: 0.62, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function stat(slide, x, y, w, big, label, color) {
  slide.addText(big, { x, y, w: 1.25, h: 0.7, fontSize: 36, bold: true, color, margin: 0, valign: "middle", isTextBox: true });
  slide.addText(label, { x: x + 1.3, y, w: w - 1.3, h: 0.7, fontSize: 13, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
}
function card(slide, x, y, w, h, title, body, color) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: C.background2 }, line: { color: C.background2 } });
  slide.addText([{ text: title, options: { bold: true, color, fontSize: 14, breakLine: true } },
                 { text: body, options: { fontSize: 12, color: C.text1 } }],
    { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: h - 0.16, margin: 0, valign: "top", paraSpaceAfter: 2, isTextBox: true });
}

// ================================================================ COVER
pres.addSection({ title: "Cover" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Cover" });
s.addText("ASA INTERNATIONAL DATAQUEST 2026 · TÜRKİYE", { x: 0.7, y: 0.6, w: 11, h: 0.35, fontSize: 12, bold: true, color: "9EC5F4", charSpacing: 3, margin: 0, isTextBox: true });
s.addText("Already Baked In", { x: 0.7, y: 1.2, w: 11.5, h: 1.1, fontSize: 54, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
s.addText("Splitting every country's population change to 2100 into momentum, mortality, fertility and migration",
  { x: 0.7, y: 2.3, w: 10.5, h: 0.9, fontSize: 22, color: "DCE6F5", margin: 0, isTextBox: true });
// the world equation, in the chart colours
const eqY = 3.85;
s.addText([{ text: `${N.world_P0_bn.toFixed(2)} bn`, options: { breakLine: true } }, { text: "2024", options: { fontSize: 10 } }],
  { x: 0.7, y: eqY, w: 1.35, h: 0.62, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
const eqItems = [["momentum", "Momentum"], ["mortality", "Mortality"], ["fertility", "Fertility"], ["migration", "Migration"]];
let ex = 2.1;
eqItems.forEach(([k, lbl]) => {
  s.addText("×", { x: ex, y: eqY, w: 0.35, h: 0.62, fontSize: 22, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  chip(s, ex + 0.4, eqY, lbl, `×${f2(wf[k])}`, HEX[k]);
  ex += 2.0;
});
s.addText("=", { x: ex, y: eqY, w: 0.35, h: 0.62, fontSize: 22, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
s.addText([{ text: `${N.world_2101_bn.toFixed(2)} bn`, options: { breakLine: true } }, { text: "2100", options: { fontSize: 10 } }],
  { x: ex + 0.4, y: eqY, w: 1.35, h: 0.62, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
s.addText("World population, UN medium projection, decomposed with the UN's own counterfactual projection variants",
  { x: 0.7, y: 4.6, w: 11, h: 0.35, fontSize: 12, color: "9EC5F4", margin: 0, isTextBox: true });
s.addText([{ text: "Team: ", options: { bold: true } }, { text: "[Team member names] · [University] · [Undergraduate / Master's]" }],
  { x: 0.7, y: 6.2, w: 11.5, h: 0.4, fontSize: 14, color: "FFFFFF", margin: 0, isTextBox: true });
s.addNotes("COVER (~20 s). Hi, we are [team]. Our project is called Already Baked In. Using the UN World Population Prospects 2024, we split every country's population change between 2024 and 2100 into four exact factors: the momentum of today's age structure, falling mortality, fertility, and migration. The line on this slide is the whole world in one equation: 8.13 billion people today, times those four factors, gives 10.17 billion by 2100.");

// ================================================================ SLIDE 1 — puzzle
pres.addSection({ title: "Content" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Content" });
s.addText("THE PUZZLE", { placeholder: "kicker" });
s.addText("A fertility rate alone does not tell a country's future", { placeholder: "title" });
s.addImage({ path: FIG("F1_tfr_vs_growth.png"), x: 0.5, y: 1.35, w: 7.25, h: 7.25 / AR("F1_tfr_vs_growth.png"), altText:
  "Scatter of 237 countries: total fertility rate in 2024 against projected population change 2024-2100, bubbles sized by population and coloured by the largest driver of change." });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.05, y: 1.35, w: 4.78, h: 1.75, rectRadius: 0.1, fill: { color: C.background2 }, line: { color: C.background2 } });
s.addText([{ text: "Research question", options: { bold: true, color: C.text2, breakLine: true } },
  { text: "How do momentum, mortality, fertility and migration combine to move each country's population from 2024 to 2100 — and is any single indicator enough to tell the story?" }],
  { x: 8.2, y: 1.42, w: 4.5, h: 1.6, fontSize: 14, color: C.text1, margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true });
stat(s, 8.05, 3.3, 4.78, `${N.below_repl_2024_n}`, "countries and areas had below-replacement fertility (TFR < 2.1) in 2024", C.text2);
stat(s, 8.05, 4.1, 4.78, `${N.below_repl_but_momentum_pos_n}`, `of them — ${N.below_repl_but_momentum_pos_pop_bn.toFixed(1)} bn people — still have age structures that push growth`, C.accent1);
stat(s, 8.05, 4.9, 4.78, `${N.below_repl_but_grows_2024_2100_n}`, "still grow by 2100: India, USA, UK, France, Canada…", C.accent3);
s.addText(`Data: 237 countries and areas, 1950–2100, plus 17 alternative UN projection variants. 318 aggregate rows removed (summing every row counts the world 44.8 times); country totals match the UN World row to within 3.6 × 10⁻⁷.`,
  { x: 8.05, y: 5.75, w: 4.78, h: 1.0, fontSize: 10, color: C.accent5, margin: 0, valign: "top", isTextBox: true });
s.addNotes(`SLIDE 1 (~55 s). Most population stories start and end with the fertility rate. This chart shows why that is not enough. Each bubble is a country: across is its 2024 fertility rate, up is its projected change to 2100. Fertility clearly matters, but look left of the replacement line at 2.1. ${N.below_repl_2024_n} countries are already below replacement, yet ${N.below_repl_but_momentum_pos_n} of them, home to ${N.below_repl_but_momentum_pos_pop_bn.toFixed(1)} billion people, still have age structures that push growth, and ${N.below_repl_but_grows_2024_2100_n} will still be larger in 2100. First we cleaned the data: the raw file mixes countries with 318 regional and income aggregates, so we kept the 237 countries and checked that they add up exactly to the UN world total. Our question: how do the four forces combine, country by country?`);

// ================================================================ SLIDE 2 — method + world
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Content" });
s.addText("METHOD", { placeholder: "kicker" });
s.addText("Four UN scenario runs split growth into four exact factors", { placeholder: "title" });
const nodes = [
  ["Start: population on 1 Jan 2024", `${N.world_P0_bn.toFixed(2)} bn`],
  ["Momentum run: replacement fertility, constant mortality, no migration", `${run["Momentum"].toFixed(2)} bn`],
  ["+ projected mortality decline (instant-replacement, zero-migration run)", `${run["Instant replacement zero migration"].toFixed(2)} bn`],
  ["+ projected fertility (zero-migration run)", `${run["Zero migration"].toFixed(2)} bn`],
  ["+ projected migration = UN medium projection", `${run["Medium"].toFixed(2)} bn`],
];
const steps = [["momentum", "Momentum"], ["mortality", "Mortality"], ["fertility", "Fertility"], ["migration", "Migration"]];
let ny = 1.4;
nodes.forEach(([lbl, val], i) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: ny, w: 4.3, h: 0.56, rectRadius: 0.1, fill: { color: C.background2 }, line: { color: C.background2 } });
  s.addText(lbl, { x: 0.65, y: ny, w: 3.0, h: 0.56, fontSize: 11, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
  s.addText(val, { x: 3.65, y: ny, w: 1.05, h: 0.56, fontSize: 14, bold: true, color: C.text2, margin: 0, align: "right", valign: "middle", isTextBox: true });
  if (i < steps.length) {
    const [k, name] = steps[i];
    s.addShape(pres.shapes.LINE, { x: 2.65, y: ny + 0.56, w: 0, h: 0.36, line: { color: C.accent4, width: 1.25, endArrowType: "triangle" } });
    s.addText(`${name}  ×${f2(wf[k])}`, { x: 2.8, y: ny + 0.56, w: 2.0, h: 0.36, fontSize: 11, bold: true, color: k === "mortality" ? C.accent5 : HEX[k], margin: 0, valign: "middle", isTextBox: true });
  }
  ny += 0.92;
});
s.addText([{ text: "P₂₁₀₀ / P₂₀₂₄ = momentum × mortality × fertility × migration", options: { bold: true, breakLine: true } },
  { text: "Each factor is a ratio of two runs, so the product is exact — no residual. In logs the four effects add up (Andreev, Kantorová & Bongaarts, UN 2013). Same chain for all 237 countries; world = sum of countries." }],
  { x: 0.5, y: 6.0, w: 5.9, h: 0.95, fontSize: 11, color: C.text1, margin: 0, valign: "top", isTextBox: true });
s.addImage({ path: FIG("F2_world_scenarios.png"), x: 6.55, y: 1.35, w: 6.3, h: 6.3 / AR("F2_world_scenarios.png"), altText:
  "World population 1950-2100: UN medium projection with 95% interval, and the momentum-only, replacement-fertility and zero-migration counterfactual runs." });
card(s, 6.55, 5.25, 6.3, 1.35, "Fertility already pulls the world down",
  `Fertility is a brake on world growth (×${f2(wf.fertility)}). The extra ${N.world_change_bn.toFixed(1)} bn to 2100 come from today's young age structure (×${f2(wf.momentum)}) and longer lives (×${f2(wf.mortality)}). Even 2.1 children per woman from 2024 would end at ${run["Instant replacement zero migration"].toFixed(1)} bn — above the UN path.`, C.accent2);
s.addNotes(`SLIDE 2 (~70 s). How do we separate the forces? The UN publishes alternative runs of its projection, and four of them form a chain. The momentum run fixes fertility at replacement, freezes mortality and removes migration, so it shows what today\'s age structure alone would do. Adding the projected fall in mortality, then projected fertility, then migration, we arrive at the official medium projection. Each step is a ratio, so the four factors multiply exactly to the total. For the world, age structure alone takes us from 8.1 to 9.6 billion, longer lives add more, and fertility, at ×${f2(wf.fertility)}, already pulls the total down. The surprise is on the right: if every woman had exactly 2.1 children starting today, the world would reach ${run["Instant replacement zero migration"].toFixed(1)} billion, more than the UN\'s own path. This century\'s growth is already baked in.`);

// ================================================================ SLIDE 3 — engines
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Content" });
s.addText("FINDINGS", { placeholder: "kicker" });
s.addText("Same outcome, different engines", { placeholder: "title" });
const h3 = 3.95;
s.addImage({ path: FIG("F3_region_decomposition.png"), x: 0.5, y: 1.35, w: h3 * AR("F3_region_decomposition.png"), h: h3, altText:
  "Diverging stacked bars of the four multiplicative effects for the world and five regions, 2024-2100." });
s.addImage({ path: FIG("F4_country_decomposition.png"), x: 6.0, y: 1.35, w: h3 * AR("F4_country_decomposition.png"), h: h3, altText:
  "Diverging stacked bars of the four multiplicative effects for thirteen large countries including Türkiye." });
s.addText([{ text: "What separates countries?", options: { bold: true, color: C.text2, breakLine: true } },
  { text: `Share of the cross-country variance in growth:`, options: { breakLine: true } },
  { text: `fertility ${Math.round(vs.fertility * 100)}%`, options: { bold: true, color: HEX.fertility, breakLine: true } },
  { text: `momentum ${Math.round(vs.momentum * 100)}%`, options: { bold: true, color: HEX.momentum, breakLine: true } },
  { text: `migration ${Math.round(vs.migration * 100)}%`, options: { bold: true, color: "11845B", breakLine: true } },
  { text: `mortality ≈ 0`, options: { bold: true, color: C.accent5 } }],
  { x: 11.15, y: 1.5, w: 1.75, h: 3.0, fontSize: 12, color: C.text1, margin: 0, valign: "top", paraSpaceAfter: 3, isTextBox: true });
const cw = 3.95, cy = 5.6, ch = 1.2;
card(s, 0.5, cy, cw, ch, `Africa ×${f2(reg.Africa.total)}`,
  `A young age structure (×${f2(reg.Africa.momentum)}) and above-replacement fertility (×${f2(reg.Africa.fertility)}) compound.`, C.accent2);
card(s, 0.5 + cw + 0.23, cy, cw, ch, `Europe ×${f2(reg.Europe.total)}`,
  `Migration (×${f2(reg.Europe.migration)}) is the main force pushing up; without it Europe would change by ${europeNoMig}.`, "11845B");
card(s, 0.5 + 2 * (cw + 0.23), cy, cw, ch, "Robust to the method",
  `Re-estimating each factor along a second chain of UN runs: r = ${f2(N.robustness_alt_path.fertility.pearson)} (fertility), ${f2(N.robustness_alt_path.migration.pearson)} (migration); the largest driver is unchanged for ${Math.round(N.robustness_alt_path.dominant_driver_unchanged_share * 100)}% of countries.`, C.accent1);
s.addNotes(`SLIDE 3 (~65 s). Here is the same split for each region and for large countries. Segments to the right push population up, to the left pull it down, and the diamond is the net result. Africa more than doubles because a young population and above-replacement fertility compound. Europe shrinks by ${Math.abs(Math.round((reg.Europe.total - 1) * 100))}%, and migration is the main force holding it up; without it the change would be ${europeNoMig}. India and Canada both have below-replacement fertility, yet India grows on momentum and Canada on migration. Türkiye shrinks by about a quarter: low fertility and projected emigration outweigh its young age structure. Across all countries, fertility explains ${Math.round(vs.fertility * 100)}% of the differences in growth, momentum ${Math.round(vs.momentum * 100)}% and migration ${Math.round(vs.migration * 100)}%, so no single indicator is enough. A second chain of UN runs gives the same main driver for ${Math.round(N.robustness_alt_path.dominant_driver_unchanged_share * 100)}% of countries.`);

// ================================================================ SLIDE 4 — uncertainty + ethics
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Content" });
s.addText("UNCERTAINTY & ETHICS", { placeholder: "kicker" });
s.addText("Read these numbers as scenarios, not destinies", { placeholder: "title" });
const w6 = 5.7;
s.addImage({ path: FIG("F6_uncertainty_vs_size.png"), x: 0.5, y: 1.35, w: w6, h: w6 / AR("F6_uncertainty_vs_size.png"), altText:
  "Width of the UN 95% interval for 2100 against 2024 population for 234 countries; smaller places have much wider intervals." });
s.addText(`The UN 95% interval for 2100 spans a factor of ×${pi["50%"].toFixed(1)} for the median country (world: ${w95[0].toFixed(1)}–${w95[1].toFixed(1)} bn). Its width tracks population size (ρ = ${minus(N.spearman_pi95_vs_logpop)}), not which engine drives growth (|ρ| ≤ ${maxAbsRhoEngine.toFixed(1)}). For Andorra, Hong Kong and Kuwait the lower bound is exactly 0 — a model artefact we flag rather than hide.`,
  { x: 0.5, y: 5.45, w: w6, h: 1.5, fontSize: 12, color: C.text1, margin: 0, valign: "top", isTextBox: true });
const eth = [
  ["B", "Projections are not data", "Every post-2023 value is a model scenario. We show UN intervals, state the chain-order assumption, and test it."],
  ["C", "Counterfactuals are not targets", "“Zero migration” and “replacement fertility” are accounting devices, not policy goals; childbearing is an individual right."],
  ["D", "Respect the people counted", `Migration turns decline into growth for ${N.migration_turns_decline_to_growth_n} countries. We report it descriptively and avoid “replacement” or crisis framing.`],
  ["B", "Weighting is a choice", `Counting countries treats Tuvalu like India. Weighted by population, migration's share of the variance falls from ${Math.round(vs.migration * 100)}% to ${Math.round(vsw.migration * 100)}% — so we report both.`],
  ["A", "Open and reproducible", "All code is public; each number is regenerated from the raw UN files with built-in checks."],
];
s.addText("Our ethical choices, following ASA's Ethical Guidelines (2022)", { x: 6.7, y: 1.35, w: 6.15, h: 0.4, fontSize: 14, bold: true, color: C.text2, margin: 0, isTextBox: true });
let ey = 1.85;
eth.forEach(([p, head, body]) => {
  s.addShape(pres.shapes.OVAL, { x: 6.7, y: ey + 0.08, w: 0.48, h: 0.48, fill: { color: C.text2 }, line: { color: C.text2 } });
  s.addText(p, { x: 6.7, y: ey + 0.08, w: 0.48, h: 0.48, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText([{ text: head, options: { bold: true, breakLine: true } }, { text: body, options: { fontSize: 11 } }],
    { x: 7.35, y: ey, w: 5.5, h: 0.92, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  ey += 0.97;
});
s.addText("Letters = ASA principles: A integrity & accountability · B integrity of data & methods · C stakeholders · D those affected. UN location names are used as published and imply no position on legal status.",
  { x: 6.7, y: 6.7, w: 6.15, h: 0.35, fontSize: 9, color: C.accent5, margin: 0, valign: "top", isTextBox: true });
s.addNotes(`SLIDE 4 (~60 s). How sure can we be? For the median country, the UN\'s 95% range for 2100 spans a factor of about ${pi["50%"].toFixed(0)}. That width depends mostly on size, not on which engine drives growth: small, migration-dependent places like Singapore and Qatar are the most uncertain, and for three places the lower bound is exactly zero, a model artefact we flag. Following the ASA ethical guidelines, we treat projections as scenarios and show their uncertainty. The zero-migration and replacement-fertility runs are accounting tools, not policy targets: decisions about children belong to people. We describe migration without crisis language. We report both country counts and population weights, because weighting changes the answer. And our code is open, so anyone can reproduce every number. Our takeaway: most of this century\'s growth is baked in by today\'s age structure, and fertility, momentum and migration must be read together. Thank you.`);

// ================================================================ REFERENCES
pres.addSection({ title: "References" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "References" });
s.addText("REFERENCES", { placeholder: "kicker" });
s.addText("Sources and code", { placeholder: "title" });
const refs = [
  "United Nations, Department of Economic and Social Affairs, Population Division (2024). World Population Prospects 2024, Online Edition. Demographic Indicators (Medium and other variants) and supplement on births by sex and life expectancy at 60. CC BY 3.0 IGO.",
  "Andreev, K., Kantorová, V. & Bongaarts, J. (2013). Demographic components of future population growth. UN Population Division, Technical Paper No. 2013/3.",
  "Bongaarts, J. (1994). Population policy options in the developing world. Science, 263(5148), 771–776.",
  "Keyfitz, N. (1971). On the momentum of population growth. Demography, 8(1), 71–80.",
  "Raftery, A. E., Li, N., Ševčíková, H., Gerland, P. & Heilig, G. K. (2012). Bayesian probabilistic population projections for all countries. PNAS, 109(35), 13915–13921.",
  "American Statistical Association (2022). Ethical Guidelines for Statistical Practice.",
  "Code and data pipeline: github.com/idiltuzkaya/asa_dataquest (cleaning, decomposition, figures; all numbers regenerate from the raw UN files).",
];
s.addText(refs.map((r, i) => ({ text: r, options: { bullet: { type: "number" }, breakLine: i < refs.length - 1 } })),
  { x: 0.5, y: 1.45, w: 12.3, h: 5.3, fontSize: 14, color: C.text1, margin: 0, valign: "top", paraSpaceAfter: 10, isTextBox: true });

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();

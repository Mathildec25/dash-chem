const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, PageOrientation, LevelFormat,
} = require("docx");

const D = JSON.parse(fs.readFileSync("/tmp/claude-0/-home-user/cccd1423-d5c4-5115-b11f-8eed18deaba5/scratchpad/si_data.json", "utf8"));
const FIG = "/home/user/dash-chem/paper/figures";

const W = 9026;                                   // usable width, A4 with 1" margins
const NAME = { "[DMIPP]": "[DMIPP]", "BuOH": "[BuOH]", "Cat. Loading": "Cat. loading",
               "Temperature": "Temperature", "Res. Time": "Res. time" };
const P = ["[DMIPP]", "BuOH", "Cat. Loading", "Temperature", "Res. Time"];
const g = (v) => (typeof v === "number" ? String(parseFloat(v.toFixed(4))) : String(v));
const f1 = (v) => Number(v).toFixed(1);
const f0 = (v) => Number(v).toFixed(0);
const f2 = (v) => Number(v).toFixed(2);
const num = (v, d) => Number(v).toFixed(d).replace("-", "\u2212");

// ---------- building blocks ----------
const body = (text, opts = {}) => new Paragraph({
  children: [new TextRun({ text, ...opts })],
  spacing: { after: 140, line: 276 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
});
const rich = (runs, opts = {}) => new Paragraph({
  children: runs.map((r) => (typeof r === "string" ? new TextRun(r) : new TextRun(r))),
  spacing: { after: 140, line: 276 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
});
const h = (text, level) => new Paragraph({
  text, heading: level, spacing: { before: 280, after: 140 },
});
const caption = (label, text) => new Paragraph({
  children: [new TextRun({ text: label + ". ", bold: true, size: 18 }),
             new TextRun({ text, size: 18 })],
  spacing: { before: 100, after: 220 }, alignment: AlignmentType.JUSTIFIED,
});

function cell(text, { header = false, width, align = AlignmentType.LEFT } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: "EDEDED" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: String(text).split("\n").map((line) => new Paragraph({
      children: [new TextRun({ text: line, bold: header, size: 18 })],
      alignment: align, spacing: { after: 0 },
    })),
  });
}

function table(headers, rows, widths, aligns) {
  const al = aligns || headers.map((_, i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER));
  return new Table({
    columnWidths: widths,
    width: { size: W, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 6, color: "808080" },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: "808080" },
      left:   { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "C8C8C8" },
      insideVertical:   { style: BorderStyle.NONE },
    },
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((t, i) => cell(t, { header: true, width: widths[i], align: al[i] })),
      }),
      ...rows.map((r) => new TableRow({
        children: r.map((t, i) => cell(t, { width: widths[i], align: al[i] })),
      })),
    ],
  });
}

function figure(file, widthPx, heightPx) {
  return new Paragraph({
    children: [new ImageRun({
      type: "png", data: fs.readFileSync(file),
      transformation: { width: widthPx, height: heightPx },
    })],
    alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 },
  });
}


// ---------- content ----------
const L = D.levels;
const n = (x) => x.toLocaleString("en-GB");
const kids = [];

const bullet = (text) => new Paragraph({
  children: [new TextRun({ text, size: 20 })],
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 80 }, alignment: AlignmentType.JUSTIFIED,
});

kids.push(new Paragraph({
  children: [new TextRun({ text: "Supporting Information", bold: true, size: 30 })],
  alignment: AlignmentType.CENTER, spacing: { after: 120 },
}));
kids.push(new Paragraph({
  children: [new TextRun({
    text: "Bayesian optimisation of the phosphorylation and post-campaign analysis of the surrogate model",
    size: 22 })],
  alignment: AlignmentType.CENTER, spacing: { after: 280 },
}));

// ---- S1 ----
kids.push(h("S1. Optimisation procedure", HeadingLevel.HEADING_1));
kids.push(body(
  "The reaction was optimised with REACTO, a Bayesian optimisation framework for chemical reactions built on BoFire and BoTorch. The reaction space and objective are declared once; a space-filling initial design is drawn and performed; all experiments recorded so far are used to fit a Gaussian-process surrogate of the yield; an acquisition function computed from that surrogate is maximised over the reaction space, and its maximiser is the next set of conditions. Experiments were proposed and performed one at a time, never batched. The surrogate is refitted from scratch at each iteration, so a campaign is determined by the set of experiments recorded and not by their order."));
kids.push(body(
  "Surrogate: single-task Gaussian process; squared-exponential (RBF) kernel with automatic relevance determination, one length scale per parameter; constant mean; fitted noise. Inputs scaled to the unit cube, yield standardised, hyperparameters set by marginal-likelihood maximisation under log-normal priors. The fitted noise standard deviation is " + g(D.noise_sd_std) + " on the standardised yield, i.e. " + f1(D.noise_sd_pct) + " percentage points."));
kids.push(body(
  "Acquisition: qLogNEI, the log-transformed noisy expected improvement, maximised over the grid subject to the process constraint. Initial design: ten points by constrained k-means over the feasible grid, after Shields et al. and Kaneko."));
kids.push(rich([
  { text: "Units. ", bold: true },
  "[DMIPP] and [BuOH] are concentrations in mol L", { text: "−1", superScript: true },
  " — the process constraint compares them directly — catalyst loading is in mol%, temperature in °C, residence time in min, yield in per cent.",
]));

// ---- S2 ----
kids.push(h("S2. Reaction space", HeadingLevel.HEADING_1));
kids.push(body(
  "All parameters are discrete: the concentrations and the temperature were declared with an increment and the optimiser searches only the resulting levels, so conditions that cannot be set on the rig are never proposed. A declared bound that does not fall on the increment is not itself a level, which is why [DMIPP] is searched to " + f1(L["[DMIPP]"].max) + " M although declared to 6.7 M. The objective is the yield, maximised over 0–100 %. One process constraint applies, [DMIPP] ≤ [BuOH], enforced exactly both when the initial design is drawn and when the acquisition function is maximised. The grid holds " + n(D.n_total) + " combinations, of which " + n(D.n_feasible) + " (" + Math.round(100 * D.n_feasible / D.n_total) + " %) satisfy it."));
kids.push(table(
  ["Parameter", "Range", "Increment", "Levels"],
  [
    ["[DMIPP] (M)",             `${f1(L["[DMIPP]"].min)} – ${f1(L["[DMIPP]"].max)}`, "0.2", String(L["[DMIPP]"].n)],
    ["[BuOH] (M)",              `${f1(L["BuOH"].min)} – ${f1(L["BuOH"].max)}`,       "0.2", String(L["BuOH"].n)],
    ["Catalyst loading (mol%)", "5.0, 7.5, 10.0",                                    "—",   String(L["Cat. Loading"].n)],
    ["Temperature (°C)",        `${f0(L["Temperature"].min)} – ${f0(L["Temperature"].max)}`, "5", String(L["Temperature"].n)],
    ["Residence time (min)",    "0.5 – 2.5",                                         "0.5", String(L["Res. Time"].n)],
  ],
  [3200, 2200, 1800, 1826]));
kids.push(caption("Table S1", "The reaction space as declared to the optimiser."));

// ---- S3 ----
kids.push(h("S3. The campaign", HeadingLevel.HEADING_1));
kids.push(body(
  "Nineteen experiments were performed: the ten of the initial design, whose best yield was " + f0(D.best_init) + " %, then nine proposed one at a time, reaching " + f0(D.best_campaign.yield) + " %."));
{
  const rows = D.experiments.map((e, i) => [
    String(i + 1), i < 10 ? "initial" : "proposed",
    f1(e["[DMIPP]"]), f1(e["BuOH"]), f1(e["Cat. Loading"]),
    f0(e["Temperature"]), f1(e["Res. Time"]), f0(e["Yield"]),
  ]);
  kids.push(table(
    ["#", "Origin", "[DMIPP]\n(M)", "[BuOH]\n(M)", "Cat.\n(mol%)", "T\n(°C)", "t\n(min)", "Yield\n(%)"],
    rows, [700, 1400, 1300, 1300, 1150, 1050, 1050, 1076]));
  kids.push(caption("Table S2", "The nineteen experiments, in the order performed."));
}

// ---- S4 ----
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h("S4. Post-campaign analysis of the surrogate", HeadingLevel.HEADING_1));
kids.push(body(
  "The campaign ends with a Gaussian process trained on every experiment performed — a model of the yield over the whole reaction space. What follows was extracted from that model, the campaign's own. Three thresholds were fixed before the analysis and applied uniformly: favourable means a predicted yield above 70 %; a posterior standard deviation σ below 15 percentage points is required everywhere; within any restricted region the arg-max of the posterior mean μ is taken. This is exploitation by design, the campaign's acquisition function having balanced predicted yield against uncertainty; here the question is not what to learn but what to trust."));

kids.push(h("S4.1 Map and predicted optimum", HeadingLevel.HEADING_2));
kids.push(body(
  "The surrogate was evaluated at all " + n(D.n_feasible) + " feasible grid points, giving μ and σ at each: μ spans " + num(D.mu_stats.min, 1) + " to " + f1(D.mu_stats.max) + " % (mean " + f1(D.mu_stats.mean) + ") and σ " + f1(D.sd_stats.min) + " to " + f1(D.sd_stats.max) + " percentage points (mean " + f1(D.sd_stats.mean) + "). The best point is [DMIPP] " + f1(D.optimum["[DMIPP]"]) + " M, [BuOH] " + f1(D.optimum["BuOH"]) + " M, " + f1(D.optimum["Cat. Loading"]) + " mol%, " + f0(D.optimum["Temperature"]) + " °C, " + f1(D.optimum["Res. Time"]) + " min, at " + f1(D.optimum.mu) + " ± " + f1(D.optimum.sd) + " %. It differs from the best experiment (" + f1(D.best_campaign["[DMIPP]"]) + " M, " + f1(D.best_campaign["BuOH"]) + " M, " + f1(D.best_campaign["Cat. Loading"]) + " mol%, " + f0(D.best_campaign["Temperature"]) + " °C, " + f1(D.best_campaign["Res. Time"]) + " min, " + f0(D.best_campaign.yield) + " % measured) in [DMIPP] alone, by two increments of 0.2 M. The surrogate therefore places no better optimum outside what the campaign found."));

kids.push(h("S4.2 Parameter influence", HeadingLevel.HEADING_2));
kids.push(body(
  "Length scales report how sharply the response turns over along each parameter; they do not measure effect size, since a long, steady slope has a long length scale and a large effect. Effects were therefore also measured directly, by sweeping each parameter across its levels with the others held at the predicted optimum, and again over 200 feasible backgrounds drawn at random (median reported); only combinations satisfying the process constraint were swept. [BuOH] has the shortest length scale of the five yet only the fourth largest median effect: it dominates near the optimum, where it moves the predicted yield by " + f1(D.effects["BuOH"]["effect at the optimum (% yield)"]) + " percentage points, and matters little elsewhere. Temperature and catalyst loading dominate throughout."));
{
  const order = ["Temperature", "Cat. Loading", "Res. Time", "BuOH", "[DMIPP]"];
  kids.push(table(
    ["Parameter", "Length scale", "Effect at the optimum\n(percentage points)", "Median effect over the space\n(percentage points)"],
    order.map((k) => [NAME[k], f1(D.effects[k]["length scale"]),
                      f1(D.effects[k]["effect at the optimum (% yield)"]),
                      f1(D.effects[k]["median effect over the space (% yield)"])]),
    [2000, 1700, 2600, 2726]));
  kids.push(caption("Table S3", "Parameter influence, ordered by median effect. Length scales are on the unit cube and comparable to one another."));
}

kids.push(h("S4.3 The favourable region", HeadingLevel.HEADING_2));
kids.push(body(
  "Of the feasible space, " + f1(D.frac_favourable) + " % is favourable — " + n(D.n_favourable) + " conditions. The marginal ranges overstate the region badly: only " + g(D.obliquity) + " % of the combinations lying inside them are in fact favourable, so the region is oblique and the parameters cannot be varied independently within the quoted ranges. Conditioned on catalyst loading, it shrinks sharply from 10 to 7.5 mol% and vanishes at 5 mol%."));
{
  const keys = Object.keys(D.extent);
  kids.push(table(
    ["Parameter", "All", "Cat. = 7.5 mol%\n(" + n(D.extent_counts["Cat. Loading = 7.5"]) + ")",
     "Cat. = 10 mol%\n(" + n(D.extent_counts["Cat. Loading = 10"]) + ")"],
    P.map((p) => [NAME[p], ...keys.map((k) => D.extent[k][p])]),
    [2100, 2200, 2363, 2363]));
  kids.push(caption("Table S4", "Extent of the favourable region, overall and conditioned on catalyst loading. No favourable condition was found at 5 mol%."));
}
kids.push(figure(FIG + "/predicted_surface.png", 610, 340));
kids.push(caption("Figure S1",
  "Predicted yield (top) and posterior standard deviation (bottom), sliced through the predicted optimum with the two remaining parameters held there (" + f1(D.optimum["Cat. Loading"]) + " mol%, " + f1(D.optimum["Res. Time"]) + " min). White contours: 70 % and 15 percentage points. Grey: forbidden by [DMIPP] ≤ [BuOH], whose extent depends on where the other concentration is held. Star, predicted optimum; large circle, best experiment; small circles, the nineteen experiments projected onto the plane of each panel, not lying in it."));

kids.push(h("S4.4 Structure of the favourable region", HeadingLevel.HEADING_2));
kids.push(body(
  "The principal-component projection of the favourable conditions (Figure S2) shows parallel bands that read as separate clusters. Colouring the same projection by temperature identifies them as one band per temperature level, PC2 loading " + f2(D.pca_loadings[1][2]) + " on temperature: they are the grid, not disconnected chemistry. Counting rather than looking settles the question — with two conditions called adjacent when they differ by one increment in exactly one parameter, the " + n(D.n_favourable) + " favourable conditions form " + (D.components === 1 ? "a single connected component" : D.components + " connected components") + "."));
kids.push(figure(FIG + "/favourable_region_pca.png", 610, 259));
kids.push(caption("Figure S2",
  "The favourable region projected onto the first two principal components of ([DMIPP], [BuOH], temperature), " + Math.round(100 * D.pca_var[0]) + " % and " + Math.round(100 * D.pca_var[1]) + " % of the variance; coloured by predicted yield (left) and by temperature (right)."));

kids.push(h("S4.5 Conditions proposed for confirmation", HeadingLevel.HEADING_2));
kids.push(body(
  "A restriction is not required to clear the 70 % threshold: a low predicted yield with a small σ is the model asserting that the restriction costs yield, which is as useful as a high one. At 5 mol% the best available is " + f1(D.plan[1]["predicted yield"]) + " % with σ = " + f1(D.plan[1].sd) + ", at the edge of what was accepted. Had no point in a region met the cap, the restriction would have returned nothing — indicating a region the campaign never explored closely enough for the surrogate to commit; that did not arise here."));
{
  const short = {
    "reference (global optimum)": "Global optimum",
    "Cat. Loading = 5": "Catalyst 5 mol%",
    "Cat. Loading = 7.5": "Catalyst 7.5 mol%",
    "[DMIPP] >= 5.5 (high)": "[DMIPP] ≥ 5.5 M",
    "[DMIPP] 4.0-5.4 (intermediate)": "[DMIPP] 4.0–5.4 M",
    "Res. Time <= 1 (short)": "Res. time ≤ 1 min",
    "combined (Cat <= 7.5, [DMIPP] >= 4, Res. Time <= 1)": "Cat. ≤ 7.5 mol%, [DMIPP] ≥ 4 M, t ≤ 1 min",
  };
  kids.push(table(
    ["Restriction", "[DMIPP]\n(M)", "[BuOH]\n(M)", "Cat.\n(mol%)", "T\n(°C)", "t\n(min)", "Predicted\nyield (%)", "σ\n(pts)"],
    D.plan.map((r) => [short[r.scenario] || r.scenario,
      f1(r["[DMIPP]"]), f1(r["BuOH"]), f1(r["Cat. Loading"]), f0(r["Temperature"]), f1(r["Res. Time"]),
      f1(r["predicted yield"]), f1(r.sd)]),
    [2500, 900, 900, 900, 780, 780, 1266, 1000]));
  kids.push(caption("Table S5", "One set of conditions per restriction: the highest predicted yield within it, subject to σ < 15 percentage points."));
}

// ---- S5 ----
kids.push(h("S5. Limitations", HeadingLevel.HEADING_1));
[
  "σ is a property of the model, not a measured reproducibility. It is calibrated only insofar as the fitted noise term reflects the true experimental reproducibility, which nineteen experiments cannot establish; the 15-point cap means ‘the campaign passed close enough to here’.",
  "Nineteen experiments in five dimensions is sparse and the map is an interpolation. What keeps it honest is that the same model reports the prediction and its uncertainty, and that the cap is applied before selection rather than after.",
  "The Gaussian process is not bounded by chemistry: it predicts slightly negative yields (to " + num(D.mu_stats.min, 1) + " %) in the coldest, most dilute corner, far from any experiment.",
  "All nine proposals were made at 10 mol% catalyst, so the surrogate is least informed at 5 and 7.5 mol% — the restrictions that ask most of it.",
  "The arg-max of μ suits confirmation, not learning; an acquisition function would choose differently, and did during the campaign.",
  "Discretisation caps resolution: an optimum falling between two levels can be approached only to within half an increment.",
].forEach((t) => kids.push(bullet(t)));

// ---- S6 ----
kids.push(h("S6. Software and reproducibility", HeadingLevel.HEADING_1));
kids.push(body(
  "Python 3.11, BoFire 0.3.1, BoTorch 0.17.0, GPyTorch 1.15.2, PyTorch 2.10.0, scikit-learn. The initial design is seeded. The optimisation strategy draws its own Monte-Carlo seed unless one is supplied, so two runs on identical data can differ where candidates score closely; the campaign was run unseeded and its final proposal was verified stable across repeated runs. Two notebooks reproducing every number, table and figure in this document are available at [URL]."));

kids.push(h("References", HeadingLevel.HEADING_1));
[
  "Ament, S.; Daulton, S.; Eriksson, D.; Balandat, M.; Bakshy, E. Unexpected Improvements to Expected Improvement for Bayesian Optimization. Adv. Neural Inf. Process. Syst. 2023.",
  "Balandat, M.; Karrer, B.; Jiang, D. R.; Daulton, S.; Letham, B.; Wilson, A. G.; Bakshy, E. BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization. Adv. Neural Inf. Process. Syst. 2020.",
  "Durholt, J. P.; et al. BoFire: Bayesian Optimization Framework Intended for Real Experiments. 2024, arXiv:2408.05040.",
  "Shields, B. J.; Stevens, J.; Li, J.; Parasram, M.; Damani, F.; Alvarado, J. I. M.; Janey, J. M.; Adams, R. P.; Doyle, A. G. Bayesian Reaction Optimization as a Tool for Chemical Synthesis. Nature 2021, 590, 89–96.",
  "Kaneko, H. Sparse Sampling for Chemical Experiments. ACS Omega 2022, 7, 47789–47795.",
].forEach((r, i) => kids.push(new Paragraph({
  children: [new TextRun({ text: `(${i + 1})  ${r}`, size: 18 })],
  spacing: { after: 90 }, alignment: AlignmentType.JUSTIFIED,
})));

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 340, hanging: 250 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838, orientation: PageOrientation.PORTRAIT },
        margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
      },
    },
    children: kids,
  }],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync("/home/user/dash-chem/paper/si/Supporting_Information.docx", b);
  console.log("written, " + b.length + " bytes, " + kids.length + " blocks");
});

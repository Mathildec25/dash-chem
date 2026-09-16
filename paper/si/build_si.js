const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, PageOrientation, LevelFormat,
} = require("docx");

const D = JSON.parse(fs.readFileSync("/tmp/claude-0/-home-user/cccd1423-d5c4-5115-b11f-8eed18deaba5/scratchpad/si_data.json", "utf8"));
const FIG = "/home/user/dash-chem/paper/figures";

const W = 9026;                                   // usable width, A4 with 1" margins
const NAME2 = { "[DMIPP]": "[DMIPP]", "BuOH": "[BuOH]", "Cat. Loading": "tBuOK loading",
                "Temperature": "Temperature", "Res. Time": "Residence time" };
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
    text: "From Mechanistic Understanding to Pilot Scale: Integrated Development of an Intensified Continuous-Flow Process for Unsymmetrical Phosphate Esters",
    italics: true, size: 20 })],
  alignment: AlignmentType.CENTER, spacing: { after: 100 },
}));
kids.push(new Paragraph({
  children: [new TextRun({ text: "Bayesian optimisation: reaction space, model and post-campaign analysis", size: 22 })],
  alignment: AlignmentType.CENTER, spacing: { after: 280 },
}));

// ---- S1 ----
kids.push(h("S1. Reaction space as declared to the optimiser", HeadingLevel.HEADING_1));
kids.push(body(
  "Each variable was declared with an increment, so the optimiser searched a finite grid rather than a continuum and never proposed a setting the pumps and the thermostatic bath could not hold. A declared bound not falling on the increment is not itself a level, which is why [DMIPP] was searched to " + f1(L["[DMIPP]"].max) + " M. One process constraint applied throughout, [DMIPP] ≤ [BuOH], enforced both when the initial design was drawn and when the acquisition function was maximised: the grid holds " + n(D.n_total) + " combinations, of which " + n(D.n_feasible) + " (" + Math.round(100 * D.n_feasible / D.n_total) + " %) satisfy it."));
kids.push(table(
  ["Variable", "Range", "Increment", "Levels"],
  [
    ["[DMIPP] (M)",             `${f1(L["[DMIPP]"].min)} – ${f1(L["[DMIPP]"].max)}`, "0.2", String(L["[DMIPP]"].n)],
    ["[BuOH] (M)",              `${f1(L["BuOH"].min)} – ${f1(L["BuOH"].max)}`,       "0.2", String(L["BuOH"].n)],
    ["tBuOK loading (mol%)",    "5.0, 7.5, 10.0",                                    "—",   String(L["Cat. Loading"].n)],
    ["Temperature (°C)",        `${f0(L["Temperature"].min)} – ${f0(L["Temperature"].max)}`, "5", String(L["Temperature"].n)],
    ["Residence time (min)",    "0.5 – 2.5",                                         "0.5", String(L["Res. Time"].n)],
  ],
  [3200, 2200, 1800, 1826]));
kids.push(caption("Table S1", "The five variables as discretised for the campaign. [DMIPP] and [BuOH] are concentrations in mol L⁻¹, so the process constraint compares them directly."));

kids.push(h("S2. Surrogate model and acquisition", HeadingLevel.HEADING_1));
kids.push(body(
  "Single-task Gaussian process: squared-exponential kernel with automatic relevance determination, one length scale per variable; constant mean; fitted noise; inputs scaled to the unit cube and the yield standardised; hyperparameters set by marginal-likelihood maximisation under log-normal priors. The fitted noise standard deviation is " + f1(D.noise_sd_pct) + " percentage points of yield. Conditions were proposed by maximising qLogNEI, the log-transformed noisy expected improvement, over the grid subject to the process constraint, one experiment per iteration, the model being refitted from scratch each time. The initial design was ten points by constrained k-means over the feasible grid."));

// ---- S3 ----
kids.push(h("S3. Experimental data", HeadingLevel.HEADING_1));
{
  const rows = D.experiments.map((e, i) => [
    String(i + 1), i < 10 ? "initial" : "BO",
    f1(e["[DMIPP]"]), f1(e["BuOH"]), f1(e["Cat. Loading"]),
    f0(e["Temperature"]), f1(e["Res. Time"]), f0(e["Yield"]),
  ]);
  kids.push(table(
    ["#", "Origin", "[DMIPP]\n(M)", "[BuOH]\n(M)", "tBuOK\n(mol%)", "T\n(°C)", "t\n(min)", "Yield\n(%)"],
    rows, [700, 1400, 1300, 1300, 1150, 1050, 1050, 1076]));
  kids.push(caption("Table S2", "The nineteen experiments of the campaign, in the order performed."));
}

// ---- S4 ----
kids.push(h("S4. Variable influence in the fitted model", HeadingLevel.HEADING_1));
{
  const order = ["Temperature", "Cat. Loading", "Res. Time", "BuOH", "[DMIPP]"];
  kids.push(table(
    ["Variable", "Length scale", "Effect at the optimum\n(percentage points)", "Median effect over the space\n(percentage points)"],
    order.map((k) => [NAME2[k], f1(D.effects[k]["length scale"]),
                      f1(D.effects[k]["effect at the optimum (% yield)"]),
                      f1(D.effects[k]["median effect over the space (% yield)"])]),
    [2000, 1700, 2600, 2726]));
  kids.push(caption("Table S3", "Quantitative basis for the trends reported in the main text, ordered by median effect. Length scales are on the unit cube and comparable to one another."));
}
kids.push(body(
  "Length scales report how sharply the predicted yield turns over along each variable, not how much it moves: a long, steady slope has a long length scale and a large effect. Effects were therefore also measured directly, by sweeping each variable across its levels with the others held at the predicted optimum, and again over 200 feasible backgrounds drawn at random (median reported). [BuOH] has the shortest length scale of the five yet only the fourth largest median effect — it dominates near the optimum, where it moves the predicted yield by " + f1(D.effects["BuOH"]["effect at the optimum (% yield)"]) + " percentage points, and matters little elsewhere."));

// ---- S5 ----
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h("S5. The region interrogated for intensification", HeadingLevel.HEADING_1));
kids.push(body(
  "Of the " + n(D.n_feasible) + " feasible grid points, " + n(D.n_favourable) + " (" + f1(D.frac_favourable) + " %) satisfy both criteria used in the main text, a predicted yield above 70 % and a posterior standard deviation below 15 percentage points. The marginal ranges in Table S4 overstate that region: only " + g(D.obliquity) + " % of the combinations lying inside them qualify, so the variables cannot be varied independently within the quoted ranges. The region is absent at 5 mol% tBuOK and shrinks sharply between 10 and 7.5 mol%. It is nonetheless a single body rather than several isolated pockets: taking two conditions as adjacent when they differ by one increment in exactly one variable, the " + n(D.n_favourable) + " conditions form " + (D.components === 1 ? "one connected component" : D.components + " connected components") + "."));
{
  const keys = Object.keys(D.extent);
  kids.push(table(
    ["Variable", "All", "tBuOK 7.5 mol%\n(" + n(D.extent_counts["Cat. Loading = 7.5"]) + ")",
     "tBuOK 10 mol%\n(" + n(D.extent_counts["Cat. Loading = 10"]) + ")"],
    P.map((p) => [NAME2[p], ...keys.map((k) => D.extent[k][p])]),
    [2100, 2200, 2363, 2363]));
  kids.push(caption("Table S4", "Extent of the region, overall and conditioned on tBuOK loading."));
}
kids.push(figure(FIG + "/predicted_surface.png", 610, 340));
kids.push(caption("Figure S1",
  "Predicted yield (top) and posterior standard deviation (bottom), sliced through the predicted optimum with the two remaining variables held there (" + f1(D.optimum["Cat. Loading"]) + " mol%, " + f1(D.optimum["Res. Time"]) + " min). White contours: 70 % and 15 percentage points. Grey: forbidden by [DMIPP] ≤ [BuOH], whose extent depends on where the other concentration is held. Star, predicted optimum; large circle, best experiment; small circles, the nineteen experiments projected onto the plane of each panel."));
kids.push(figure(FIG + "/favourable_region_pca.png", 610, 259));
kids.push(caption("Figure S2",
  "The same region projected onto the first two principal components of ([DMIPP], [BuOH], temperature), " + Math.round(100 * D.pca_var[0]) + " % and " + Math.round(100 * D.pca_var[1]) + " % of the variance, coloured by predicted yield (left) and by temperature (right). The banding is the temperature grid — PC2 loads " + f2(D.pca_loadings[1][2]) + " on temperature — not disconnected chemistry."));

// ---- S6 ----
kids.push(h("S6. Conditions returned under the process constraints", HeadingLevel.HEADING_1));
{
  const short = {
    "reference (global optimum)": "Unconstrained optimum",
    "Cat. Loading = 5": "tBuOK 5 mol%",
    "Cat. Loading = 7.5": "tBuOK 7.5 mol%",
    "[DMIPP] >= 5.5 (high)": "[DMIPP] ≥ 5.5 M",
    "[DMIPP] 4.0-5.4 (intermediate)": "[DMIPP] 4.0–5.4 M",
    "Res. Time <= 1 (short)": "t ≤ 1 min",
    "combined (Cat <= 7.5, [DMIPP] >= 4, Res. Time <= 1)": "tBuOK ≤ 7.5 mol%, [DMIPP] ≥ 4 M, t ≤ 1 min",
  };
  kids.push(table(
    ["Restriction", "[DMIPP]\n(M)", "[BuOH]\n(M)", "tBuOK\n(mol%)", "T\n(°C)", "t\n(min)", "Predicted\nyield (%)", "σ\n(pts)"],
    D.plan.map((r) => [short[r.scenario] || r.scenario,
      f1(r["[DMIPP]"]), f1(r["BuOH"]), f1(r["Cat. Loading"]), f0(r["Temperature"]), f1(r["Res. Time"]),
      f1(r["predicted yield"]), f1(r.sd)]),
    [2500, 900, 900, 900, 780, 780, 1266, 1000]));
  kids.push(caption("Table S5", "The highest predicted yield within each restriction, subject to σ < 15 percentage points. The three conditions carried forward in the main text are rows 5 ([DMIPP] 4.0–5.4 M), 6 (t ≤ 1 min) and 3 (tBuOK 7.5 mol%)."));
}
kids.push(body(
  "A restriction is not required to clear the 70 % threshold, so a low predicted yield with a small σ is the model asserting that the restriction costs yield: at 5 mol% tBuOK the best available is " + f1(D.plan[1]["predicted yield"]) + " % with σ = " + f1(D.plan[1].sd) + ", at the edge of what was accepted. Had no point in a restricted region met the σ cap, that restriction would have returned nothing, indicating a region the campaign never sampled closely enough for the model to commit; this did not arise."));

// ---- S7 ----
kids.push(h("S7. Limitations of the model-based analysis", HeadingLevel.HEADING_1));
[
  "σ is the surrogate's posterior standard deviation, not a measured reproducibility. It is calibrated only insofar as the fitted noise term reflects the experimental reproducibility, which nineteen experiments cannot establish; the 15-point cap means that the campaign passed close enough to a given region, not that the yield there is known to ± 15 %.",
  "All nine proposals were made at 10 mol% tBuOK, so the model is least informed at 5 and 7.5 mol% — the restrictions that ask most of it.",
  "Taking the highest predicted yield within a restriction is exploitation, appropriate for selecting conditions to confirm but not for further learning; an acquisition function would choose differently. Discretisation caps resolution at half an increment.",
].forEach((t) => kids.push(bullet(t)));

// ---- S8 ----
kids.push(h("S8. Software", HeadingLevel.HEADING_1));
kids.push(body(
  "Python 3.11, BoFire 0.3.1, BoTorch 0.17.0, GPyTorch 1.15.2, PyTorch 2.10.0, scikit-learn. The initial design is seeded. The optimisation strategy draws its own Monte-Carlo seed unless one is supplied, so two runs on identical data can differ where candidate conditions score closely; the campaign was run unseeded and its final proposal was verified stable across repeated runs. Two notebooks reproducing every number, table and figure in this section are available at [URL]."));

kids.push(h("References", HeadingLevel.HEADING_1));
[
  "Ament, S.; Daulton, S.; Eriksson, D.; Balandat, M.; Bakshy, E. Unexpected Improvements to Expected Improvement for Bayesian Optimization. Adv. Neural Inf. Process. Syst. 2023.",
  "Balandat, M.; Karrer, B.; Jiang, D. R.; Daulton, S.; Letham, B.; Wilson, A. G.; Bakshy, E. BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization. Adv. Neural Inf. Process. Syst. 2020.",
  "Durholt, J. P.; et al. BoFire: Bayesian Optimization Framework Intended for Real Experiments. 2024, arXiv:2408.05040.",
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

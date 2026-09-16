const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, PageOrientation,
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
const kids = [];

kids.push(new Paragraph({
  children: [new TextRun({ text: "Supporting Information", bold: true, size: 32 })],
  alignment: AlignmentType.CENTER, spacing: { after: 160 },
}));
kids.push(new Paragraph({
  children: [new TextRun({
    text: "Bayesian optimisation of the phosphorylation: campaign design and post-campaign analysis of the surrogate model",
    size: 24 })],
  alignment: AlignmentType.CENTER, spacing: { after: 320 },
}));

kids.push(h("S1. Optimisation framework", HeadingLevel.HEADING_1));
kids.push(body(
  "The reaction was optimised with REACTO, a Bayesian optimisation framework for chemical reactions built on BoFire and BoTorch. A campaign is a closed loop with four steps. The reaction space and the objective are declared once. A space-filling initial design is drawn inside that space and performed. Every experiment recorded so far is then used to fit a Gaussian-process surrogate of the yield, an acquisition function computed from that surrogate is maximised over the reaction space, and the maximiser is the next set of conditions to run. The chemist performs it, records the yield, and the surrogate is refitted."));
kids.push(body(
  "Experiments were proposed one at a time and performed one at a time; nothing was batched and nothing was simulated. Because the surrogate is refitted from scratch at each iteration, a campaign is determined by the set of experiments recorded and not by the order in which they were run."));
kids.push(rich([
  "Throughout this document ", { text: "[DMIPP]", bold: true }, " and ", { text: "[BuOH]", bold: true },
  " are concentrations in mol L", { text: "−1", superScript: true },
  ". The process constraint compares them directly and would be meaningless otherwise. Catalyst loading is in mol%, temperature in °C, residence time in min, and yield in per cent.",
]));

kids.push(h("S2. Reaction space, objective and constraint", HeadingLevel.HEADING_1));
kids.push(body(
  "Every parameter is discrete. Concentrations and temperature are continuous quantities but were declared with an increment, and the optimiser searches only the resulting levels; catalyst loading and residence time are discrete by nature. The optimiser therefore never proposes conditions that cannot be set on the rig. A declared bound that does not fall on the increment is not itself a level, which is why [DMIPP] is searched to " + g(L["[DMIPP]"].max) + " M although it was declared to 6.7 M."));
kids.push(table(
  ["Parameter", "Range", "Increment", "Levels"],
  [
    ["[DMIPP] (M)",        `${f1(L["[DMIPP]"].min)} – ${f1(L["[DMIPP]"].max)}`, "0.2",       String(L["[DMIPP]"].n)],
    ["[BuOH] (M)",         `${f1(L["BuOH"].min)} – ${f1(L["BuOH"].max)}`,       "0.2",       String(L["BuOH"].n)],
    ["Catalyst loading (mol%)", "5.0, 7.5, 10.0",                                 "—",         String(L["Cat. Loading"].n)],
    ["Temperature (°C)",   `${f0(L["Temperature"].min)} – ${f0(L["Temperature"].max)}`, "5", String(L["Temperature"].n)],
    ["Residence time (min)", "0.5 – 2.5",                                     "0.5",       String(L["Res. Time"].n)],
  ],
  [3200, 2200, 1800, 1826]));
kids.push(caption("Table S1", "The reaction space as declared to the optimiser."));
kids.push(rich([
  "The objective was the yield, to be maximised, over a useful range of 0–100 %. A single process constraint applied, ",
  { text: "[DMIPP] ≤ [BuOH]", bold: true },
  ", known before any experiment was run and enforced exactly: it was imposed both when the initial design was drawn and when the acquisition function was maximised, so conditions violating it were never proposed. The grid holds " + D.n_total.toLocaleString("en-GB") + " combinations, of which " + D.n_feasible.toLocaleString("en-GB") + " (" + Math.round(100 * D.n_feasible / D.n_total) + " %) satisfy the constraint.",
]));

kids.push(h("S3. Initial design", HeadingLevel.HEADING_1));
kids.push(body(
  "Ten initial experiments were selected by constrained k-means, following the approach of Shields et al. and of Kaneko. The grid was enumerated, conditions violating the process constraint were discarded, the survivors were min–max scaled, and k-means was run with ten clusters; the feasible point nearest each centroid was retained. The design therefore covers the reaction space evenly within the feasible region, which a design drawn over the enclosing box and filtered afterwards would not."));

kids.push(h("S4. Surrogate model and acquisition function", HeadingLevel.HEADING_1));
kids.push(body(
  "The surrogate is a single-task Gaussian process with a squared-exponential (RBF) kernel under automatic relevance determination — one length scale per parameter — a constant mean and a fitted noise term. Inputs are scaled to the unit cube and the yield is standardised before fitting, so the length scales are directly comparable to one another. Hyperparameters are obtained by maximising the marginal likelihood under log-normal priors, which is what keeps them identifiable from nineteen points in five dimensions. The fitted noise standard deviation is " + g(D.noise_sd_std) + " on the standardised yield, i.e. " + g(D.noise_sd_pct) + " percentage points of yield; it is inferred from the data rather than measured, and it sets the floor of the posterior uncertainty everywhere."));
kids.push(body(
  "Conditions were proposed by maximising qLogNEI, the log-transformed noisy expected improvement. Expected improvement scores a candidate by how much it is expected to exceed the best yield obtained so far under the posterior; the noisy variant treats recorded yields as noisy realisations rather than as ground truth, which is the appropriate assumption for a bench measurement; the log formulation is a numerically stable reparametrisation that keeps gradients informative where the probability of improvement is very small. This is what balances exploration against exploitation without either being specified by hand: a candidate scores well either because its predicted yield is high or because the posterior there is wide enough that it might be."));

kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h("S5. The campaign", HeadingLevel.HEADING_1));
kids.push(body(
  "Nineteen experiments were performed: the ten of the initial design, then nine proposed one at a time. The best yield of the initial design was " + f0(D.best_init) + " %; the campaign reached " + f0(D.best_campaign.yield) + " %."));
{
  const rows = D.experiments.map((e, i) => [
    String(i + 1), i < 10 ? "initial" : "proposed",
    f1(e["[DMIPP]"]), f1(e["BuOH"]), f1(e["Cat. Loading"]),
    f0(e["Temperature"]), f1(e["Res. Time"]), f0(e["Yield"]),
  ]);
  kids.push(table(
    ["#", "Origin", "[DMIPP]\n(M)", "[BuOH]\n(M)", "Cat.\n(mol%)", "T\n(°C)", "t\n(min)", "Yield\n(%)"],
    rows, [700, 1400, 1300, 1300, 1150, 1050, 1050, 1076]));
  kids.push(caption("Table S2", "The nineteen experiments of the campaign, in the order performed."));
}

kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h("S6. Post-campaign analysis of the surrogate", HeadingLevel.HEADING_1));
kids.push(body(
  "The campaign ends with more than its best experiment: it ends with a fitted Gaussian process, a model of the yield over the whole reaction space, trained on every experiment performed. What follows was extracted from that model, the campaign's own, once the campaign was closed."));
kids.push(body(
  "The logic of this section is the inverse of the campaign's. During optimisation, conditions were chosen by an acquisition function that deliberately balances predicted yield against uncertainty: an experiment is worth running partly because its outcome is unknown. Here the question is no longer what to learn but what to trust, and every selection below takes the highest predicted yield subject to the surrogate being confident there. Three thresholds were fixed before the analysis and applied uniformly: a predicted yield above 70 % defines the favourable region; a posterior standard deviation below 15 percentage points is required everywhere; and within any region of interest the arg-max of the posterior mean is taken."));

kids.push(h("S6.1 Prediction over the reaction space", HeadingLevel.HEADING_2));
kids.push(body(
  "The surrogate was evaluated at every one of the " + D.n_feasible.toLocaleString("en-GB") + " feasible grid points — against the nineteen actually performed — giving a posterior mean μ and standard deviation σ at each. Over that space μ ranges from " + num(D.mu_stats.min, 1) + " to " + f1(D.mu_stats.max) + " % (mean " + f1(D.mu_stats.mean) + " %) and σ from " + f1(D.sd_stats.min) + " to " + f1(D.sd_stats.max) + " percentage points (mean " + f1(D.sd_stats.mean) + "). This step costs one Gaussian-process evaluation per grid point and no experiments at all."));

kids.push(h("S6.2 The predicted optimum", HeadingLevel.HEADING_2));
kids.push(body(
  "The best point of the map lies at [DMIPP] = " + f1(D.optimum["[DMIPP]"]) + " M, [BuOH] = " + f1(D.optimum["BuOH"]) + " M, " + f1(D.optimum["Cat. Loading"]) + " mol% catalyst, " + f0(D.optimum["Temperature"]) + " °C and " + f1(D.optimum["Res. Time"]) + " min, with a predicted yield of " + f1(D.optimum.mu) + " ± " + f1(D.optimum.sd) + " %. It differs from the best experiment performed (" + f1(D.best_campaign["[DMIPP]"]) + " M, " + f1(D.best_campaign["BuOH"]) + " M, " + f1(D.best_campaign["Cat. Loading"]) + " mol%, " + f0(D.best_campaign["Temperature"]) + " °C, " + f1(D.best_campaign["Res. Time"]) + " min, " + f0(D.best_campaign.yield) + " % measured) in [DMIPP] alone, by two increments of 0.2 M, every other parameter being identical; the predicted yield is the same to within a tenth of a point and the posterior there is narrow. The surrogate therefore does not believe the campaign stopped short, and the value of the map lies elsewhere: in what it says about the extent of that optimum and about the regions the optimiser left behind."));

kids.push(h("S6.3 What the yield responds to", HeadingLevel.HEADING_2));
kids.push(body(
  "Two readings were taken, which answer different questions. Length scales say how fast the surrogate believes the yield varies along each parameter, in units of that parameter's full range: a short length scale means the response turns over quickly. This is a statement about the shape of the response and not about how much the parameter matters, since a long, steady slope has a long length scale and a large effect."));
kids.push(body(
  "The second reading answers that question directly. Each parameter was walked across its levels with the others held at the predicted optimum, and the spread of the predicted yield recorded; because a single background can flatter or flatten an effect, the sweep was repeated over 200 feasible backgrounds drawn at random and the median reported. Only combinations satisfying the process constraint were swept."));
{
  const order = ["Temperature", "Cat. Loading", "Res. Time", "BuOH", "[DMIPP]"];
  const rows = order.map((k) => [
    NAME[k],
    g(D.effects[k]["length scale"]),
    g(D.effects[k]["effect at the optimum (% yield)"]),
    g(D.effects[k]["median effect over the space (% yield)"]),
  ]);
  kids.push(table(
    ["Parameter", "Length scale", "Effect at the optimum\n(percentage points)", "Median effect over the space\n(percentage points)"],
    rows, [2000, 1700, 2600, 2726]));
  kids.push(caption("Table S3", "Parameter influence, ordered by median effect. Length scales are on the unit cube and are comparable to one another."));
}
kids.push(body(
  "The two columns disagree for [BuOH], which has the shortest length scale of the five and yet only the fourth largest effect across the space. The disagreement is informative rather than contradictory: [BuOH] dominates near the optimum, where it moves the predicted yield by " + g(D.effects["BuOH"]["effect at the optimum (% yield)"]) + " percentage points, and matters much less elsewhere. The effect is local, which is a statement about interactions and not about relevance. Temperature and catalyst loading are the parameters whose influence is felt throughout the space."));

kids.push(h("S6.4 The favourable region", HeadingLevel.HEADING_2));
kids.push(body(
  "The conditions predicted above 70 % with σ below 15 percentage points number " + D.n_favourable.toLocaleString("en-GB") + ", i.e. " + g(D.frac_favourable) + " % of the feasible space. Their extent can be described in two ways, which must not be confused."));
{
  const keys = Object.keys(D.extent);
  const rows = P.map((p) => [NAME[p], ...keys.map((k) => D.extent[k][p])]);
  const headers = ["Parameter", "All", "Cat. = 7.5 mol%\n(" + D.extent_counts["Cat. Loading = 7.5"] + ")",
                   "Cat. = 10 mol%\n(" + D.extent_counts["Cat. Loading = 10"].toLocaleString("en-GB") + ")"];
  kids.push(table(headers, rows, [2100, 2200, 2363, 2363]));
  kids.push(caption("Table S4", "Extent of the favourable region: marginal ranges overall, and conditioned on catalyst loading. No favourable condition was found at 5 mol%."));
}
kids.push(body(
  "The marginal ranges — the span of each parameter taken one at a time — are what one is tempted to quote, and they overstate the region badly: only " + g(D.obliquity) + " % of the combinations lying inside them are in fact favourable. The region is oblique, meaning the parameters cannot be varied independently within their quoted ranges without leaving it. The ranges conditioned on catalyst loading are what can be worked with, and they show that the region shrinks sharply when the loading is reduced from 10 to 7.5 mol% and vanishes at 5 mol%."));

kids.push(figure(FIG + "/predicted_surface.png", 610, 340));
kids.push(caption("Figure S1",
  "Predicted yield (top) and its posterior standard deviation (bottom), sliced through the predicted optimum with the two remaining parameters held there (catalyst loading " + f1(D.optimum["Cat. Loading"]) + " mol%, residence time " + f1(D.optimum["Res. Time"]) + " min). White contours mark 70 % and 15 percentage points. Grey areas are forbidden by [DMIPP] ≤ [BuOH]; how much of a panel they occupy depends on where the other concentration is held, so with [BuOH] fixed at its optimal " + f1(D.optimum["BuOH"]) + " M nothing above [DMIPP] = " + f1(D.optimum["BuOH"]) + " M is available at all. The star marks the predicted optimum and the large circle the best experiment; small circles are the nineteen experiments, drawn at their coordinates in the plane of each panel regardless of their other parameters — they are projected onto the slice, not lying in it."));

kids.push(h("S6.5 Structure of the favourable region", HeadingLevel.HEADING_2));
kids.push(body(
  "Whether the favourable conditions form one body or several disconnected islands matters, since a single body can be traversed continuously whereas islands would mean distinct operating regimes. Projecting the region onto its first two principal components (Figure S2) gives clean parallel bands that read as separate clusters and are nothing of the sort: colouring the same projection by temperature identifies them as one band per temperature level. They are the grid, not the chemistry, a reading confirmed by the loadings, PC2 lying almost entirely along temperature (" + g(D.pca_loadings[1][2]) + ")."));
kids.push(body(
  "The question was therefore settled by counting rather than by eye. Two favourable conditions were called adjacent when they differ by one increment in exactly one parameter, and the connected components of the resulting graph were counted: the " + D.n_favourable.toLocaleString("en-GB") + " conditions form " + (D.components === 1 ? "a single component" : D.components + " components") + ". The region is one body in the only sense available on a discrete domain — reachable by single steps without ever leaving it."));
kids.push(figure(FIG + "/favourable_region_pca.png", 610, 259));
kids.push(caption("Figure S2",
  "The favourable region projected onto the first two principal components of ([DMIPP], [BuOH], temperature), accounting for " + Math.round(100 * D.pca_var[0]) + " % and " + Math.round(100 * D.pca_var[1]) + " % of the variance. The same points are coloured by predicted yield (left) and by temperature (right); the banding is the temperature grid, not disconnected chemistry."));

kids.push(h("S6.6 Confirmatory experiments", HeadingLevel.HEADING_2));
kids.push(body(
  "The map was finally used to answer the questions that arise once a campaign is over, each of which restricts the reaction space differently: whether the catalyst loading can be reduced, whether a high substrate concentration still works, whether the residence time can be cut. For each restriction the highest predicted yield within it was taken, subject to σ below 15 percentage points."));
{
  const short = {
    "reference (global optimum)": "Global optimum",
    "Cat. Loading = 5": "Catalyst 5 mol%",
    "Cat. Loading = 7.5": "Catalyst 7.5 mol%",
    "[DMIPP] >= 5.5 (high)": "[DMIPP] ≥ 5.5 M",
    "[DMIPP] 4.0-5.4 (intermediate)": "[DMIPP] 4.0–5.4 M",
    "Res. Time <= 1 (short)": "Res. time ≤ 1 min",
    "combined (Cat <= 7.5, [DMIPP] >= 4, Res. Time <= 1)": "Catalyst ≤ 7.5 mol%, [DMIPP] ≥ 4 M, res. time ≤ 1 min",
  };
  const rows = D.plan.map((r) => [
    short[r.scenario] || r.scenario,
    f1(r["[DMIPP]"]), f1(r["BuOH"]), f1(r["Cat. Loading"]), f0(r["Temperature"]), f1(r["Res. Time"]),
    f1(r["predicted yield"]), f1(r.sd),
  ]);
  kids.push(table(
    ["Restriction", "[DMIPP]\n(M)", "[BuOH]\n(M)", "Cat.\n(mol%)", "T\n(°C)", "t\n(min)", "Predicted\nyield (%)", "σ\n(pts)"],
    rows, [2500, 900, 900, 900, 780, 780, 1266, 1000]));
  kids.push(caption("Table S5", "Conditions proposed for confirmation, one per restriction: the highest predicted yield within the restriction, subject to σ < 15 percentage points."));
}
kids.push(body(
  "Note what is and is not required. A restriction returns the highest predicted yield it can find while staying below the uncertainty cap; it is not required to clear the 70 % threshold. A row predicting a low yield with a small σ is therefore a result in its own right — the model asserting that the restriction costs yield — and is as useful to a process chemist as a row predicting a high one. Halving the catalyst loading to 5 mol% is the clearest case: the best the model can offer is " + f1(D.plan[1]["predicted yield"]) + " %, and it says so with a σ of " + f1(D.plan[1].sd) + " points, at the edge of what was accepted."));
kids.push(body(
  "Had no point in a restricted region satisfied the uncertainty cap, that region would have returned nothing, which is itself a finding: it would mean the campaign never explored it closely enough for the surrogate to commit. That did not arise here, though the 5 mol% row sits close enough to the cap to be read as marginal."));

kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h("S7. Limitations", HeadingLevel.HEADING_1));
kids.push(body(
  "σ is a property of the model, not of the chemistry. The posterior standard deviation says how far the surrogate's prediction might be from what the surrogate itself would predict given more data of the same kind. It is calibrated only to the extent that the fitted noise term reflects the true experimental reproducibility, which nineteen experiments cannot establish. The 15-point cap should be read as ‘the campaign passed close enough to here’, not as a confidence interval on a measurement."));
kids.push(body(
  "The map is an interpolation. Nineteen experiments in five dimensions is sparse. What keeps the exercise honest is that the same model reports both the prediction and its uncertainty, and that the uncertainty cap is applied before any point is selected rather than after."));
kids.push(body(
  "The surrogate is not bounded by chemistry. A Gaussian process on a standardised yield knows nothing about 0 and 100 %, and predicts slightly negative yields (to " + num(D.mu_stats.min, 1) + " %) in the coldest, most dilute corner of the space, far from any experiment. Nothing above depends on that corner, but it is a reminder that the map is a smooth interpolation of nineteen numbers and not a kinetic model."));
kids.push(body(
  "The campaign shaped what can be said. All nine proposals were made at 10 mol% catalyst, so that is where the surrogate is informed and its confidence highest. The restrictions at 5 and 7.5 mol% ask the model to speak about a part of the space the optimiser left behind early, which is precisely why they were asked."));
kids.push(body(
  "Selecting the arg-max of μ is right for confirmation and wrong for learning. An acquisition function would have chosen differently, and did, during the campaign itself. The two procedures are complementary and should not be swapped."));
kids.push(body(
  "Discretisation has a price. The finer the increment the larger the search, and a parameter whose true optimum falls between two levels can only be approached to within half an increment."));

kids.push(h("S8. Software and reproducibility", HeadingLevel.HEADING_1));
kids.push(body(
  "Computations were performed with Python 3.11, BoFire 0.3.1, BoTorch 0.17.0, GPyTorch 1.15.2, PyTorch 2.10.0 and scikit-learn. The initial design was seeded and is reproducible. The optimisation strategy draws its own Monte-Carlo seed unless one is supplied, so two runs on identical data can differ wherever two candidate conditions score closely; the campaign was run without an explicit seed and is therefore reproducible from its recorded experiments, and the final proposal was verified to be stable across repeated runs."));
kids.push(body(
  "Two notebooks reproduce every number, table and figure in this document — one for the campaign, one for the post-campaign analysis — and are available in the repository accompanying this work [URL]. They are provided for readers who wish to inspect or reuse the procedure; no code is required to follow the account given here."));

kids.push(h("References", HeadingLevel.HEADING_1));
[
  "Ament, S.; Daulton, S.; Eriksson, D.; Balandat, M.; Bakshy, E. Unexpected Improvements to Expected Improvement for Bayesian Optimization. Adv. Neural Inf. Process. Syst. 2023.",
  "Balandat, M.; Karrer, B.; Jiang, D. R.; Daulton, S.; Letham, B.; Wilson, A. G.; Bakshy, E. BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization. Adv. Neural Inf. Process. Syst. 2020.",
  "Durholt, J. P.; et al. BoFire: Bayesian Optimization Framework Intended for Real Experiments. 2024, arXiv:2408.05040.",
  "Rasmussen, C. E.; Williams, C. K. I. Gaussian Processes for Machine Learning; MIT Press: Cambridge, MA, 2006.",
  "Shields, B. J.; Stevens, J.; Li, J.; Parasram, M.; Damani, F.; Alvarado, J. I. M.; Janey, J. M.; Adams, R. P.; Doyle, A. G. Bayesian Reaction Optimization as a Tool for Chemical Synthesis. Nature 2021, 590, 89–96.",
  "Kaneko, H. Sparse Sampling for Chemical Experiments. ACS Omega 2022, 7, 47789–47795.",
].forEach((r, i) => kids.push(new Paragraph({
  children: [new TextRun({ text: `(${i + 1})  ${r}`, size: 20 })],
  spacing: { after: 110 }, alignment: AlignmentType.JUSTIFIED,
})));

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 22 } } } },
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

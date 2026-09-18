# Answer sheet: nb3_svg_and_imputation

Reference for the questions posed in the notebook. Written after you have worked through
the notebook and thought about each question yourself.

## Question 1 (Section 1, the graph again)

> The absolute Moran's I values shrink noticeably from `k=6` to `k=30` even though the
> top-50 gene identities barely move. Why would averaging over more neighbours
> systematically pull every I towards zero, regardless of which genes they are?

Moran's I compares a cell's value to the average value of its spatial neighbours, weighted
by the connectivity matrix. As `k` grows, that average is computed over a larger and more
heterogeneous set of cells, most of which sit further from the focal cell. Real spatial
patterns have a finite length scale: once the neighbourhood extends beyond that length
scale, the added neighbours carry progressively less information about the focal cell's
specific value, because they are simply too far away for the underlying biology to still
correlate them. Averaging over more, more distant neighbours acts as a low-pass filter, and
for a large enough neighbourhood the average approaches the same quantity for every cell,
the global mean of the gene. Correlating a value against something that is converging to a
constant necessarily drives the correlation, and therefore Moran's I, toward zero, purely as
a property of the averaging rather than of the gene's true spatial structure.

This is also why absolute Moran's I values are not comparable across different graph
constructions. Only the ranking of genes under a fixed graph is meaningful, and even that
ranking should be checked for stability across choices of `k`, which is exactly what this
section does.

## Question 2 (Section 3, conditioning on cell type)

> `TUBB2B` and `SERPINA3` are two of the genes that do survive conditioning. What would you
> check next before calling either one "spatially regulated within epithelial cells"?

Surviving the within-cell-type conditioning check rules out the most common confounder in
this notebook: the gene is not simply marking which cells are `epithelial_tumor` and where
those cells happen to sit. It does not by itself establish active spatial regulation. Before
making that stronger claim, four things are worth checking.

First, whether the within-type spatial pattern corresponds to a finer subdivision of cell
state that the coarse `epithelial_tumor` label does not capture, for example a proliferative
or hypoxic subregion of the tumour. A finer, unmodelled confounder can reproduce this result
exactly as the original cell-type confounder did, just one level down.

Second, whether the pattern is robust to the graph and normalisation choices explored earlier
in the notebook. The same caveats that applied to the global gene list apply again within a
single cell type, and a result that only appears under one specific graph or normalisation is
weaker evidence than one that persists across several.

Third, whether the gene has a plausible biological driver for spatial patterning specifically
within this compartment, such as a known gradient (oxygen, nutrient availability, distance to
stroma) or a known transcriptional programme, rather than treating the statistic alone as an
explanation.

Fourth, whether the pattern replicates in the second field of view or in an independent
sample. A two-field-of-view crop cannot on its own distinguish a real, recurring biological
gradient from a feature specific to this particular piece of tissue.

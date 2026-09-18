# Answer sheet: nb2_cell_cell_communication

Reference for the questions posed in the notebook. Written after you have worked through
the notebook and thought about each question yourself.

## Question 1 (Section 1, permuting coordinates)

> `fibroblast_stromal -> endothelial` via `MMP2/PECAM1` scores near the top. Would you trust
> that pair more or less than a pair between two cell types that are abundant but rarely
> adjacent? What would you need to check?

You should trust the `fibroblast_stromal -> endothelial` pair more, provided the two cell
types are actually found near each other in the tissue, which is biologically plausible here:
fibroblasts commonly surround and remodel the perivascular matrix, PECAM1 (CD31) is a
canonical endothelial marker, and MMP2 is a matrix metalloproteinase secreted by stromal
fibroblasts. A non-spatial score cannot see adjacency at all, so it cannot tell you whether a
high-scoring pair reflects two cell types that touch and potentially signal locally, or two
cell types that are simply both abundant and both express their respective genes at high,
consistent levels across the tissue regardless of where either one sits. Both situations
produce the same non-spatial score.

What you would need to check before trusting either pair: explicit spatial evidence, such as
neighbourhood enrichment between the two cell types or the spatially weighted bivariate score
from Section 2 of this notebook, to confirm the two types are actually adjacent more often
than chance. An abundant-but-rarely-adjacent pair can still be a robust and reproducible
non-spatial signal, but it is then a claim about two cell types independently expressing
complementary genes across the tissue, which is a different and weaker biological claim than
local juxtacrine or short-range paracrine communication. A non-spatial score alone cannot
distinguish the two, which is exactly the gap this notebook exists to close.

## Question 2 (Section 4, shuffling cell type labels)

> Why might `CXCR4` (a receptor with an established ligand pair in the LR analysis above)
> show weaker NCEM coupling than `LYZ` (a marker gene with no plausible ligand-receptor story
> for T/NK cells at all)?

The two results are not in conflict once the two methods are recognised as testing different
things. The spatially weighted LR score in Section 2 flags `CXCL12`/`CXCR4` as spatially
co-varying using a local bivariate statistic computed across many cells, a comparatively
low bar that a modest, real, diffuse chemokine gradient can satisfy. NCEM asks a much more
specific question: does this one gene's expression in this one receiver cell type depend
linearly on the precise neighbourhood composition around each individual cell, fit on a few
hundred points. `CXCR4` transcript level in T/NK cells may be driven mostly by the cell's own
activation or differentiation state rather than by exactly which cell types are locally
present, so the coupling to neighbourhood composition specifically can be genuinely weak even
while a broader spatial gradient that the LR test's local score is sensitive to still exists
at a coarser scale.

`LYZ` shows the reverse pattern for a different reason: no plausible receptor biology places
it in T/NK cells at all, yet it couples strongly to the local myeloid fraction. That
combination, a marker gene for a cell type appearing in a different neighbouring cell type in
proportion to how much of that neighbouring type is present, is the expected signature of
transcript spillover across a segmentation boundary rather than of genuine signalling.

The general lesson is that NCEM coupling strength is not a proxy for how well established the
underlying biology is. It is a proxy for how strongly one gene's level in one receiver type
moves with one neighbourhood variable, and that quantity can be large for a segmentation
artefact and small for real but diffuse or cell-intrinsic biology. This is why the notebook
insists on the shuffle-null control for every individual (receiver, gene, radius) result
rather than trusting the direction of either result on its own.

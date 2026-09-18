# Answer sheet: nb1_niches_and_clustering

Reference for the questions posed in the notebook. Written after you have worked through
the notebook and thought about each question yourself.

## Question 1 (Section 3, comparing niche flavours)

> Even after choosing niche counts of similar order of magnitude (8, 10, 21), pairwise ARI
> stays below 0.21. All three methods see the same graph and the same cells, but not the
> same feature space. What does that tell you about how much a "niche" depends on the
> definition rather than the tissue?

Agreement between the three flavours tracks feature space, not niche count. The two
flavours that both start from continuous expression, `utag` (spatially smoothed expression)
and `cellcharter` (an scVI embedding of expression), agree with each other at ARI = 0.207.
`neighborhood`, which clusters the composition of discrete Leiden labels rather than
continuous expression, agrees with neither of the other two (0.019 and 0.016), even though
all three see the identical graph and the identical set of cells.

This is evidence that a niche is largely a property of the method's definition of "feature"
before clustering, not a single latent spatial pattern that any reasonable method should
recover. Two methods built on related representations of expression converge on similar
answers because they are, in an important sense, clustering similar information, only
processed differently. The method built on a categorically different representation
(composition of pre-existing discrete labels) answers a different question: "what mixture of
already-assigned cell type labels surrounds this cell" is not the same question as "what does
the smoothed or embedded expression around this cell look like," and there is no reason to
expect the two answers to coincide.

The practical implication is that before comparing niche calls across studies or methods, the
first thing to check is not resolution or graph choice, since this dataset shows those matter
less than feature space does for overall agreement. Report which representation a niche
method clusters on with the same care as the graph and the resolution.

## Question 2 (Section 5, evaluating niches without a reference)

> PAS on the raw expression clusters is close to 0.5, coin-flip agreement with your spatial
> neighbours. Why would that be true even for a correct clustering of cell types, and what
> does it tell you about what PAS is actually measuring?

PAS measures spatial contiguity of a partition, not the biological correctness of a
partition. Individual cells of a given type are not expected to sit only next to other cells
of the same type; a T cell can be a correctly labelled T cell while its immediate physical
neighbours are epithelial, myeloid, or stromal cells, because cell identity and spatial
position are governed by different biological processes (lineage and differentiation versus
tissue architecture and local recruitment). A cell-type clustering can therefore be entirely
correct as an identity assignment and still score near 0.5 on PAS, since PAS only asks
whether a cell's label matches the majority label of its spatial neighbours, and for
dispersed cell types that majority vote is close to a coin flip by construction.

This shows that PAS and CHAOS are diagnostics for spatial smoothness, not for whether a
clustering is biologically meaningful. A method can score well on both by ignoring expression
entirely and drawing arbitrary but contiguous blobs on the tissue. They are necessary checks
on a niche method (a niche is supposed to be spatially coherent) but they say nothing at all
about whether the *cell type* assignments feeding into a composition-based niche method, or
the expression values feeding into an aggregation-based one, are themselves correct.

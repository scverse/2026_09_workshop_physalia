# Day 3 — Niches, cell-cell communication, and spatially variable genes

Work through these in order. All three pick up the same object: the two-field-of-view
10x Xenium human breast cancer crop from Day 1 (7,275 cells, 280 genes), QC-filtered the
same way. Notebook 3 also makes a brief detour to the Visium H&E object for a method that
needs a regular grid.

| | Notebook | Block | What it covers |
|---|---|---|---|
| 1 | [`nb1_niches_and_clustering.ipynb`](nb1_niches_and_clustering.ipynb) | 1 | Marker-based cell typing, the spatial graph as a hyperparameter, three niche-detection flavours (neighbourhood / UTAG / CellCharter), resolution, and evaluating niches with and without a reference |
| 2 | [`nb2_cell_cell_communication.ipynb`](nb2_cell_cell_communication.ipynb) | 2 | Non-spatial vs. spatially weighted ligand-receptor inference (LIANA), linear NCEM built from scratch, and the segmentation-spillover callback to Day 1 |
| 3 | [`nb3_svg_and_imputation.ipynb`](nb3_svg_and_imputation.ipynb) | 3 | Spatially variable genes with Moran's I, the graph/normalisation/cell-type confounders, sepal as a contrasting method, and SVG pattern modules |

Imputation (cross-modality prediction of unmeasured genes) is covered in Block 3's talk
only this year — there is no imputation hands-on section. Frame it strictly as predicting
genes that were never measured; denoising already-measured genes is ResolVI's job, covered
in the AI session later the same day.

## Before you start

- Pick the kernel **"Physalia spatial omics"** (top right). It is already installed.
- The shared data at `/opt/workshop/data` is **read-only**. Use `import paths` and write
  anything you produce to `paths.OUT`.
- Notebook 1 computes a marker-based cell type annotation for the Xenium table (the table
  does not ship one). All three notebooks look for it via `paths.precomputed("xenium_celltypes.h5ad")`,
  which checks the shared, read-only cache at `/opt/workshop/data/precomputed/` first, then
  your own `paths.OUT`, and recomputes it inline only if neither has it — so any notebook can
  still be started from a fresh kernel, same convention as Day 1.
- Notebook 1's niche comparison also needs a precomputed scVI embedding
  (`xenium_scvi_latent.npy`) for the CellCharter niche flavour — training scVI live is not
  something everyone can do at once on a shared CPU box. This one ships precomputed in
  `/opt/workshop/data/precomputed/` and has no live-recompute fallback: if `paths.precomputed`
  can't find it there or in your own `paths.OUT`, the cell raises `FileNotFoundError` with the
  training call shown (commented) so you can see what produced it.

## If you fall behind

Every notebook is stored with its outputs, so you can read ahead or catch up without
re-running anything. Each notebook's setup cell reapplies Day 1's QC filter directly rather
than depending on a cache, so you can start any of the three from a fresh kernel.

## Exercises

Each notebook ends with an exercise and an empty cell. As in Day 1, they are the part worth
doing afterwards if the hands-on runs short — none of them need anything beyond what the
notebook already showed you.

## The through-line

The same spatial graph gets built three times across these notebooks — once per block —
and the same lesson repeats each time: the graph, the resolution, the normalisation, and the
radius are all choices you made, not properties of the tissue. Block 2's coordinate-
permutation check and Block 3's cell-type-conditioning check are the two single cells worth
remembering if you remember nothing else.

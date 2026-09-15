# Day 1 — Preprocessing and data foundations

Work through these in order. Each notebook picks up where the previous one left off, on the
same dataset: a two-field-of-view crop of a 10x Xenium human breast cancer section
(7,275 cells, 280 genes, 1.1 million transcripts).

| | Notebook | Session | What it covers |
|---|---|---|---|
| 1 | [`nb1_spatialdata_objects.ipynb`](nb1_spatialdata_objects.ipynb) | 1 | The `SpatialData` element model, coordinate systems, plotting, cropping |
| 2 | [`nb2_segmentation_qc.ipynb`](nb2_segmentation_qc.ipynb) | 2.1 | The five metrics that diagnose an imaging-based segmentation |
| 3 | [`nb3_segmentation_sopa.ipynb`](nb3_segmentation_sopa.ipynb) | 2.2 | Re-segmenting with SOPA + Cellpose, and comparing against the vendor |
| 4 | [`nb4_spatial_statistics_squidpy.ipynb`](nb4_spatial_statistics_squidpy.ipynb) | 3 | Spatial graphs, neighbourhood enrichment, co-occurrence, Ripley |

## Before you start

- Pick the kernel **"Physalia spatial omics"** (top right). It is already installed.
- The shared data at `/opt/workshop/data` is **read-only**. Use `import paths` and write
  anything you produce to `paths.OUT`.
- Every notebook starts by locating the repository root so that `import paths` works. That
  cell is safe to re-run. Run the cells in order.

## If you fall behind

The notebooks are stored with their outputs, so you can read ahead or catch up without
re-running anything. Notebook 4 picks up the filtered object that notebook 2 saves, and falls
back to recomputing it if you skipped ahead — so any notebook can be started from a fresh
kernel.

## Exercises

Each notebook ends with an exercise and an empty cell. The exercises are the part worth doing
afterwards if we run out of time — none of them need more than what the notebook already
showed you.

# Day 3 — AI-driven methods

| | Notebook | Session | What it covers |
|---|---|---|---|
| 1 | [`nb_morphology_mofa.ipynb`](nb_morphology_mofa.ipynb) | 8.1 | H&E foundation-model features per Visium spot, and one factor model for image + expression |

The dataset changes today: a 10x Visium section of a coronal mouse brain with its H&E image
(2,688 spots, 18,078 genes), staged at `/opt/workshop/data/visium_hne.zarr`. Visium measures
whole-transcriptome expression in 55 µm spots. The image model sees exactly those 55 µm: one tile
per spot, cropped to the spot's bounding box, with no overlap between neighbours.

## Nothing heavy runs live

Two steps are pre-computed and shipped in `checkpoints/`, because neither belongs on a shared
CPU server with 25 people on it:

| File | What | Made by |
|---|---|---|
| `visium_hne_hoptimus0_embeddings.npz` | 1,536 image features per spot from H-optimus-0 (1.1B parameters) | `scripts/precompute_hne_embeddings.py` |
| `mofa_visium_hne.h5` | MOFA-FLEX fitted to expression and image jointly (several minutes on CPU) | `scripts/prefit_mofa_visium_hne.py` |
| `mofa_visium_hne_shuffled.h5` | the negative control: same model, image features shuffled across spots | `scripts/prefit_mofa_visium_hne.py` |
| `mofa_visium_hne_rna_only.h5`, `mofa_visium_hne_img_only.h5` | the same model on each view alone | `scripts/prefit_mofa_visium_hne.py` |

The notebook has an optional cell that fits the model live with a short training budget. Its
factors will not match the shipped model exactly — that is expected.

## Before you start

- Kernel **"Physalia spatial omics"**, as on Days 1 and 2.
- Anything you save goes to `paths.OUT`, never into the repository.

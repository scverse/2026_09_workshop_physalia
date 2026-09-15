"""Fit the MOFA-FLEX models that notebooks/day_3/nb_morphology_mofa.ipynb loads.

Instructor-only. One CPU fit takes several minutes on an M1 Pro and would be slower on a
shared teaching server, so participants load the results instead of fitting them.

    PHYSALIA_DATA=~/physalia_data pixi run python scripts/prefit_mofa_visium_hne.py

Writes four models to notebooks/day_3/checkpoints/, all with identical data preparation,
options, number of factors and seed:

- mofa_visium_hne.h5              expression (2000 HVGs) + H&E embeddings, jointly
- mofa_visium_hne_shuffled.h5     the same, with embeddings permuted across spots — the
                                  negative control: no shared structure left to find
- mofa_visium_hne_rna_only.h5     expression alone
- mofa_visium_hne_img_only.h5     H&E embeddings alone

The data preparation here must stay identical to the notebook's `build_mudata` cell.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import anndata as ad
import mofaflex as mfl
import mudata as md
import numpy as np
import pandas as pd
import scanpy as sc
import spatialdata as sd

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PHYSALIA_DATA", "/opt/workshop/data"))
CKPT = Path(os.environ.get("MOFA_CKPT", REPO / "notebooks" / "day_3" / "checkpoints"))
N_FACTORS = 10
SEED = 42
MAX_EPOCHS = int(os.environ.get("MOFA_MAX_EPOCHS", "10000"))  # lowered only for smoke tests


def build_mudata(adata: ad.AnnData, emb_path: Path, shuffle: bool = False, seed: int = SEED) -> md.MuData:
    # expression: raw counts -> median-depth normalisation -> shifted log -> 2000 HVGs chosen on counts
    rna = adata.raw.to_adata()
    rna.layers["counts"] = rna.X.copy()
    sc.pp.normalize_total(rna, target_sum=None)
    sc.pp.log1p(rna)
    sc.pp.highly_variable_genes(rna, flavor="seurat_v3", n_top_genes=2000, layer="counts")
    rna = rna[:, rna.var["highly_variable"].to_numpy()].copy()
    rna.X = rna.X.toarray()
    del rna.layers["counts"]

    # image: H&E foundation-model embedding per spot, each feature z-scored
    z = np.load(emb_path, allow_pickle=False)
    order = pd.Index(z["spot_id"]).get_indexer(adata.obs["spot_id"].astype(str))
    assert (order >= 0).all(), "embedding file does not cover every spot"
    x = z["embedding"][order].astype(np.float32)
    x = (x - x.mean(axis=0)) / np.clip(x.std(axis=0), 1e-6, None)
    if shuffle:
        x = x[np.random.default_rng(seed).permutation(len(x))]

    img = ad.AnnData(x, obs=pd.DataFrame(index=adata.obs_names.copy()))
    img.var_names = [f"emb_{i}" for i in range(x.shape[1])]
    return md.MuData({"rna": rna, "img": img})


def fit(mdata: md.MuData, path: Path) -> None:
    t0 = time.time()
    model = mfl.MOFAFLEX(
        mdata,
        mfl.DataOptions(plot_data_overview=False, subset_var=None),
        mfl.ModelOptions(n_factors=N_FACTORS, likelihoods="Normal"),
        mfl.TrainingOptions(device="cpu", seed=SEED, max_epochs=MAX_EPOCHS, save_path=path),
    )
    r2 = model.get_r2(ordered=True)["group_1"]
    r2 = r2 if r2.shape[0] == N_FACTORS else r2.T
    print(f"wrote {path.name} in {time.time() - t0:.0f}s, {len(model.training_loss)} epochs, {path.stat().st_size / 1e6:.1f} MB")
    print(r2.round(3).T.to_string())
    print("total R² per view:", r2.sum().round(3).to_dict(), flush=True)


def main() -> None:
    adata = sd.read_zarr(DATA / "visium_hne.zarr")["adata"]
    (emb_path,) = sorted(CKPT.glob("visium_hne_*_embeddings.npz"))
    print(f"embeddings: {emb_path.name}")
    full = build_mudata(adata, emb_path)
    fit(full, CKPT / "mofa_visium_hne.h5")
    fit(build_mudata(adata, emb_path, shuffle=True), CKPT / "mofa_visium_hne_shuffled.h5")
    fit(md.MuData({"rna": full["rna"]}), CKPT / "mofa_visium_hne_rna_only.h5")
    fit(md.MuData({"img": full["img"]}), CKPT / "mofa_visium_hne_img_only.h5")


if __name__ == "__main__":
    main()

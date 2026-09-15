"""Render the Session 8.1 slide figures from the committed models.

Instructor-only, and not part of the notebook: it re-renders the teaching figures as standalone
PNGs at 220 dpi for slides. It fits nothing — everything is read from
notebooks/day_3/checkpoints — so it is safe to re-run.

    PHYSALIA_DATA=~/physalia_data pixi run python scripts/export_slide_figures.py

Writes seven files to ~/Desktop/physalia_slide_assets (override with SLIDE_ASSETS):

    S8_1_tiles_by_region.png        one spot tile per anatomical region
    S8_1_variance_explained.png     R² per view across models, including the 100-PC variant
    S8_1_shared_vs_null.png         per-factor R², joint model against the shuffled null
    S8_1_factor_maps.png            F6 (shared) and F8 (image-only), maps plus extreme tiles
    S8_1_library_size_confound.png  every factor against log library size
    S8_1_morans_i.png               spatial smoothness, joint factors against the null
    S8_1_view_balance.png           expression R² at 1536 image features vs 100 PCs

The PNGs themselves are not committed. Colours follow the course style card.
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import mofaflex as mfl
import numpy as np
import pandas as pd
import spatialdata as sd
import squidpy as sq
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import spearmanr

INK, RULE, MID = "#1A1A1A", "#D8D8D8", "#767676"
TEAL, RED, SLATE, STEEL = "#4C9A8F", "#C0605A", "#7A8FA6", "#4A7BA7"
DIVERGING = LinearSegmentedColormap.from_list("steel_red", [STEEL, "#FFFFFF", RED])

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PHYSALIA_DATA", "/opt/workshop/data"))
CKPT = REPO / "notebooks" / "day_3" / "checkpoints"
OUT = Path(os.environ.get("SLIDE_ASSETS", Path.home() / "Desktop" / "physalia_slide_assets"))
OUT.mkdir(parents=True, exist_ok=True)

# The 100-PC variant is a balance check, not teaching material, so its models are not in the
# repository and these three numbers are hard-coded. To regenerate: take build_mudata() from
# scripts/prefit_mofa_visium_hne.py, replace the image view with PCA(n_components=100) of the
# z-scored embeddings (89.3% of their variance), and fit with the same options and seed.
# Its image R² is measured in PC space and is NOT comparable to the 1536-feature models.
PC100_EXPRESSION_R2 = 0.462
PC100_IMAGE_R2_PC_SPACE = 0.317
PC100_VARIANCE_KEPT = 0.893

mpl.rcParams.update({
    "figure.dpi": 220, "savefig.dpi": 220, "figure.facecolor": "white", "savefig.facecolor": "white",
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": RULE, "axes.titlecolor": INK,
    "xtick.color": MID, "ytick.color": MID, "axes.grid": False, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "legend.frameon": False,
})


def save(fig, name):
    path = OUT / f"S8_1_{name}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path.name}  {path.stat().st_size / 1e3:.0f} kB")


sdata = sd.read_zarr(DATA / "visium_hne.zarr")
adata, spots = sdata["adata"], sdata["spots"]
adata.obsm["spatial"] = np.c_[spots.geometry.x, spots.geometry.y][adata.obs["spot_id"].to_numpy()]
xy = adata.obsm["spatial"]
CROP = round(2 * spots["radius"].median())
hne = sdata["hne"]["scale0"]["image"]


def tile(i, size=CROP):
    x, y = np.round(xy[i]).astype(int)
    h = size // 2
    return hne.isel(y=slice(y - h, y - h + size), x=slice(x - h, x - h + size)).transpose("y", "x", "c").values


files = {"joint": "mofa_visium_hne", "joint_shuffled": "mofa_visium_hne_shuffled",
         "rna_only": "mofa_visium_hne_rna_only", "img_only": "mofa_visium_hne_img_only"}
models = {k: mfl.MOFAFLEX.load(CKPT / f"{v}.h5", map_location="cpu") for k, v in files.items()}
R2, F = {}, {}
for k, m in models.items():
    r = m.get_r2(ordered=True)["group_1"]
    R2[k] = (r if r.shape[0] == m.n_factors else r.T).set_axis([f"F{i}" for i in range(1, m.n_factors + 1)], axis=0)
    f = m.get_factors(ordered=True)["group_1"].loc[adata.obs_names]
    F[k] = f.set_axis([f"F{i}" for i in range(1, f.shape[1] + 1)], axis=1)

log_lib = np.log10(np.asarray(adata.raw.to_adata().X.sum(axis=1)).ravel())
rng = np.random.default_rng(0)

# ------------------------------------------------------------ 1. tiles by region
regions = ["Cortex_2", "Pyramidal_layer_dentate_gyrus", "Fiber_tract", "Thalamus_1", "Striatum", "Lateral_ventricle"]
fig, axs = plt.subplots(1, 6, figsize=(12, 2.6))
for ax, region in zip(axs, regions):
    i = rng.choice(np.flatnonzero(adata.obs["cluster"] == region))
    ax.imshow(tile(i))
    ax.add_patch(plt.Circle((CROP / 2 - 0.5, CROP / 2 - 0.5), spots["radius"].median(), fill=False, color=INK, lw=1.1, ls="--"))
    ax.set_title(region.replace("_", "\n"), fontsize=8.5, linespacing=1.25)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(RULE)
fig.suptitle("One tile per spot: the 55 µm that spot measured, nothing else", y=1.09, fontsize=11, fontweight="bold")
fig.text(0.5, -0.06, "76 px crop → 224 px for the model = 0.25 µm/px, against the 0.5 µm/px it was trained at · dashed circle = the spot",
         ha="center", fontsize=8.5, color=MID)
save(fig, "tiles_by_region")

# ------------------------------------------------------------ 2. variance explained
labels = ["expression\nalone", "joint,\n1536 image\nfeatures", "joint,\nimage as\n100 PCs", "joint, 1536,\nimage shuffled", "image\nalone"]
expr = [R2["rna_only"]["rna"].sum(), R2["joint"]["rna"].sum(), PC100_EXPRESSION_R2, R2["joint_shuffled"]["rna"].sum(), np.nan]
imag = [np.nan, R2["joint"]["img"].sum(), np.nan, R2["joint_shuffled"]["img"].sum(), R2["img_only"]["img"].sum()]
fig, ax = plt.subplots(figsize=(8.6, 4.6))
x = np.arange(5); w = 0.38
for k, (vals, colour, hatch, name) in enumerate([(expr, STEEL, "", "expression view"), (imag, SLATE, "///", "image view")]):
    ax.bar(x + (k - 0.5) * w, np.nan_to_num(vals), w, color=colour, hatch=hatch, edgecolor="white", label=name)
    for xi, v in zip(x + (k - 0.5) * w, vals):
        if not np.isnan(v):
            ax.text(xi, v + 0.016, f"{v:.3f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
ax.text(2 + 0.19, 0.02, "no comparable image bar", ha="center", va="bottom", fontsize=7.5, color=MID, rotation=90)
ax.set(xticks=x, ylim=(0, 0.92), ylabel="total R² over 10 factors")
ax.set_xticklabels(labels, fontsize=8.5)
ax.legend(loc="upper left", fontsize=9)
ax.set_title("The bigger view wins: 1536 image features cost expression variance, 100 PCs do not")
gain = PC100_EXPRESSION_R2 - R2["joint"]["rna"].sum()
fig.text(0.5, -0.065, f"cutting the image view from 1536 features to 100 PCs recovers +{gain:.3f} of expression variance",
         ha="center", fontsize=9.5, color=TEAL, fontweight="bold")
fig.text(0.5, -0.155, f"100 PCs keep {PC100_VARIANCE_KEPT:.1%} of the image variance. That model's image R² ({PC100_IMAGE_R2_PC_SPACE}) is measured in PC space and is NOT\n"
                      f"comparable to {R2['joint']['img'].sum():.3f} on 1536 features, so no image bar is drawn for it — compare the expression bars across models.",
         ha="center", fontsize=8, color=MID)
save(fig, "variance_explained")

# ------------------------------------------------------------ 3. shared vs null
fig, ax = plt.subplots(figsize=(6.4, 5.6))
ax.axvline(0.01, color=RULE, lw=1)
ax.axhline(0.01, color=RULE, lw=1)
n_joint = int(((R2["joint"]["rna"] >= 0.01) & (R2["joint"]["img"] >= 0.01)).sum())
n_null = int(((R2["joint_shuffled"]["rna"] >= 0.01) & (R2["joint_shuffled"]["img"] >= 0.01)).sum())
ax.scatter(R2["joint_shuffled"]["rna"], R2["joint_shuffled"]["img"], s=80, marker="s", facecolor="white",
           edgecolor=RED, lw=1.5, label=f"image shuffled — {n_null} of 10 pass")
ax.scatter(R2["joint"]["rna"], R2["joint"]["img"], s=85, marker="o", color=TEAL, label=f"joint model — {n_joint} of 10 pass")
for f in ["F1", "F6", "F8"]:
    ax.annotate(f, (R2["joint"].loc[f, "rna"], R2["joint"].loc[f, "img"]), xytext=(8, -3),
                textcoords="offset points", fontsize=9.5, fontweight="bold")
ax.annotate("F8: image only,\nexpression R² = 0.000", (R2["joint"].loc["F8", "rna"], R2["joint"].loc["F8", "img"]),
            xytext=(44, -30), textcoords="offset points", fontsize=8.5, color=INK,
            arrowprops=dict(arrowstyle="-", color=MID, lw=0.9))
ax.annotate(f"F1: expression R² {R2['joint'].loc['F1', 'rna']:.3f},\nabove the null's {R2['joint_shuffled']['rna'].max():.3f}",
            (R2["joint"].loc["F1", "rna"], R2["joint"].loc["F1", "img"]), xytext=(-118, -34),
            textcoords="offset points", fontsize=8.5, color=INK, arrowprops=dict(arrowstyle="-", color=MID, lw=0.9))
ax.text(0.0125, 0.003, "1% of a view's variance", fontsize=8, color=MID)
ax.set(xlabel="R² in expression", ylabel="R² in image", xlim=(-0.004, 0.108), ylim=(0, 0.108))
ax.legend(loc="lower right", fontsize=9)
ax.set_title(f"A 1% threshold calls {n_null} shuffled factors “shared”, so the cut is meaningless")
save(fig, "shared_vs_null")

# ------------------------------------------------------------ 4. factor maps + extreme tiles
fig = plt.figure(figsize=(13.5, 8.6))
gs = fig.add_gridspec(2, 5, width_ratios=[1.6, 1, 1, 1, 1], hspace=0.30, wspace=0.22)
blocks = [("F6", "shared — myelin genes, fiber-tract tiles", "Mbp · Plp1 · Mobp · Mag"),
          ("F8", "image only — stain and focus across the slide", "no gene programme: R² 0.000")]
for row, (f, claim, genes) in enumerate(blocks):
    ax = fig.add_subplot(gs[row, 0])
    v = F["joint"][f].to_numpy()
    lim = np.abs(v).max()
    sc = ax.scatter(xy[:, 0], xy[:, 1], c=v, cmap=DIVERGING, vmin=-lim, vmax=lim, s=5, linewidths=0)
    ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")
    r = R2["joint"].loc[f]
    ax.set_title(f"{f} — {claim}\nR² expression {r['rna']:.3f} · image {r['img']:.3f} · {genes}", fontsize=9, loc="left")
    cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.08)
    cb.outline.set_edgecolor(RULE); cb.ax.tick_params(colors=MID, labelsize=7)
    order = np.argsort(v)
    for k, i in enumerate(np.r_[order[::-1][:2], order[:2]]):
        tax = fig.add_subplot(gs[row, k + 1])
        tax.imshow(tile(i))
        end = "red end" if k < 2 else "blue end"
        tax.set_title(f"{end} · {adata.obs['cluster'].iloc[i].replace('_', ' ')}\nscore {v[i]:+.2f}", fontsize=8)
        tax.set_xticks([]); tax.set_yticks([])
        for s in tax.spines.values():
            s.set_color(RED if k < 2 else STEEL); s.set_linewidth(1.8)
fig.suptitle("One factor is tissue biology, the other is the slide", y=0.98, fontsize=11.5, fontweight="bold")
save(fig, "factor_maps")

# ------------------------------------------------------------ 5. library-size confound
rows = [{"label": f"{'joint' if n == 'joint' else 'expr-only'} {f}", "rho": spearmanr(F[n][f], log_lib)[0]}
        for n in ["joint", "rna_only"] for f in F[n].columns]
conf = pd.DataFrame(rows).set_index("label").sort_values("rho")
n_tracking = int((conf["rho"].abs() >= 0.5).sum())
fig, ax = plt.subplots(figsize=(7.2, 6.6))
ax.barh(conf.index, conf["rho"], color=[RED if abs(v) >= 0.5 else SLATE for v in conf["rho"]], edgecolor="white")
for y, v in enumerate(conf["rho"]):
    ax.text(v + (0.022 if v >= 0 else -0.022), y, f"{v:+.2f}", va="center", ha="left" if v >= 0 else "right",
            fontsize=8.5, fontweight="bold" if abs(v) >= 0.5 else "normal")
ax.axvline(0, color=RULE, lw=1)
ax.annotate("F1 — the joint model's\nmost expression-loaded factor", xy=(conf.loc["joint F1", "rho"], list(conf.index).index("joint F1")),
            xytext=(-0.82, list(conf.index).index("joint F1") + 5.2), fontsize=8.5, color=RED, ha="left",
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.3, connectionstyle="arc3,rad=-0.2"))
ax.set(xlabel="Spearman ρ with log library size", xlim=(-0.85, 0.85))
ax.tick_params(axis="y", labelsize=8)
ax.set_title(f"Depth normalisation did not remove depth: {n_tracking} factors still track it")
fig.text(0.5, -0.02, "red = |ρ| ≥ 0.5 · library size is itself spatial here (Moran's I 0.48, 47% of its variance between regions)",
         ha="center", fontsize=8.5, color=MID)
save(fig, "library_size_confound")

# ------------------------------------------------------------ 6. Moran's I
sq.gr.spatial_neighbors_knn(adata, n_neighs=6)
cols = []
for n in ["joint", "joint_shuffled"]:
    for f in F[n].columns:
        adata.obs[f"{n}_{f}"] = F[n][f].to_numpy()
        cols.append(f"{n}_{f}")
moran = sq.gr.spatial_autocorr(adata, mode="moran", attr="obs", genes=cols, n_perms=None, copy=True, show_progress_bar=False)
adata.obs = adata.obs.drop(columns=cols)
joint_I = moran.loc[[c for c in cols if c.startswith("joint_F")], "I"].to_numpy()
shuf_I = moran.loc[[c for c in cols if c.startswith("joint_shuffled")], "I"].to_numpy()
fig, ax = plt.subplots(figsize=(7.2, 4.4))
for xpos, vals, colour, marker, name in [(0, joint_I, TEAL, "o", "joint model"), (1, shuf_I, RED, "s", "image shuffled")]:
    ax.scatter(np.full(len(vals), xpos) + rng.normal(0, 0.03, len(vals)), vals, s=80, marker=marker,
               facecolor=colour if marker == "o" else "white", edgecolor=colour, lw=1.5, label=name)
    ax.hlines(np.median(vals), xpos - 0.17, xpos + 0.17, color=colour, lw=2.5)
    ax.text(xpos + 0.23, np.median(vals), f"median {np.median(vals):.2f}\nrange {vals.min():.2f}–{vals.max():.2f}",
            va="center", fontsize=9, fontweight="bold")
ax.set(xticks=[0, 1], xticklabels=["joint factors", "shuffled-image factors"], ylabel="Moran's I on the 6 nearest spots",
       ylim=(-0.06, 1.0), xlim=(-0.35, 1.6))
ax.legend(loc="lower left", fontsize=9)
ax.set_title("Spatial smoothness separates real factors from the null; R² does not")
save(fig, "morans_i")

# ------------------------------------------------------------ 7. view balance
bal = pd.Series({"expression\nalone": R2["rna_only"]["rna"].sum(), "joint,\n1536 image features": R2["joint"]["rna"].sum(),
                 "joint,\n100 image PCs": PC100_EXPRESSION_R2})
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.bar(bal.index, bal.to_numpy(), 0.55, color=[SLATE, RED, TEAL], edgecolor="white")
for xi, v in enumerate(bal):
    ax.text(xi, v + 0.012, f"{v:.3f}", ha="center", fontsize=10, fontweight="bold")
ax.axhline(bal.iloc[0], color=RULE, lw=1, ls="--")
ax.set(ylabel="total R² in the expression view", ylim=(0, 0.62))
ax.tick_params(axis="x", labelsize=9)
ax.set_title("Shrink the image view and expression variance comes back")
fig.text(0.5, -0.04, f"100 PCs keep {PC100_VARIANCE_KEPT:.1%} of the image variance · image R² is not comparable across these models (PC space vs 1536 features)",
         ha="center", fontsize=8, color=MID)
save(fig, "view_balance")

print(f"\nwrote 7 figures to {OUT}")

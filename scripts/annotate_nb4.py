"""Annotate the five Leiden clusters in nb4 and re-run it on the shared data.

Run on the workshop server, where /opt/workshop/data exists:

    pixi run python scripts/annotate_nb4.py

Why: nb4 computed every spatial statistic on unnamed Leiden clusters, so each
result answered "does cluster 0 sit next to cluster 3", which is not a
biological question. This inserts a cluster-annotation step (justified by
rank_genes_groups) and switches nhood_enrichment / co_occurrence / ripley /
centrality_scores onto the named cell types.

Cluster calls, read off the differential expression:
  0 KRT7 TACSTD2 EPCAM JUP DSC2          -> Epithelial
  1 SERPINA3 AQP1 BACE2 EPCAM            -> Epithelial
  2 TOP2A MKI67 CENPF PCLAF EPCAM        -> Proliferating
  3 LYZ CD68 PTPRC ITGAX CD163           -> Myeloid
  4 LUM POSTN CXCL12 SFRP4 PDGFRB        -> Fibroblast

Note: ~79% of this section is epithelium, and there is no T/B/endothelial/mast
cluster at 280 genes. We annotate what the data supports and say so on the slide.
"""

import json
import re
import shutil
import sys
import time
from pathlib import Path

NB = Path("notebooks/day_1/nb4_spatial_statistics_squidpy.ipynb")


def cell(kind, src):
    c = {"cell_type": kind, "metadata": {}, "source": src.splitlines(keepends=True)}
    if kind == "code":
        c |= {"outputs": [], "execution_count": None}
    return c


MD1 = """## 1b. Name the clusters before asking about neighbourhoods

`leiden` gives us numbers. Every statistic below asks *"do these two groups sit together"*, and
"does cluster 0 sit next to cluster 3" is not a biological question. So we annotate first, from
the differentially expressed genes of each cluster.

This is the ordinary, defensible way to annotate, and it is close to what 10x themselves do for
this panel — they transfer labels from matched single-cell data (Janesick et al. 2023,
*Nat Commun*), reporting 86% of cells unambiguously assigned.
"""

CODE1 = '''sc.tl.rank_genes_groups(adata, "leiden", method="wilcoxon")
for c in adata.obs["leiden"].cat.categories:
    top = sc.get.rank_genes_groups_df(adata, group=c).head(10)["names"].tolist()
    print(f"cluster {c} (n={(adata.obs['leiden'] == c).sum():5d}): {', '.join(top)}")
'''

MD2 = """The read-out is unambiguous:

| cluster | markers | call |
|---|---|---|
| 0 | `KRT7`, `TACSTD2`, **`EPCAM`**, `JUP`, `DSC2` | epithelial |
| 1 | `SERPINA3`, `AQP1`, `BACE2`, **`EPCAM`** | epithelial |
| 2 | **`TOP2A`, `MKI67`, `CENPF`, `PCLAF`** + `EPCAM` | epithelial, proliferating |
| 3 | `LYZ`, `CD68`, **`PTPRC`**, `ITGAX`, `CD163` | myeloid |
| 4 | `LUM`, `POSTN`, `CXCL12`, `SFRP4`, `PDGFRB` | fibroblast |

Two things to notice, because both shape every result below. **About 79% of this section is
epithelium** — it is a tumour-dominated sample. And there is **no T-cell, B-cell, endothelial or
mast cluster**: those cells are present in the tissue, but at 280 genes they do not separate into
clusters of their own. Annotate what the data supports, and state the limit.
"""

CODE2 = '''cell_type_map = {
    "0": "Epithelial",
    "1": "Epithelial",
    "2": "Proliferating",
    "3": "Myeloid",
    "4": "Fibroblast",
}
adata.obs["cell_type"] = adata.obs["leiden"].map(cell_type_map).astype("category")

# one stable colour per cell type, reused by every squidpy plot below
palette = {
    "Epithelial": "#7A8FA6",
    "Proliferating": "#4A7BA7",
    "Myeloid": "#E8912A",
    "Fibroblast": "#4C9A8F",
}
adata.uns["cell_type_colors"] = [
    palette[c] for c in adata.obs["cell_type"].cat.categories
]

print(adata.obs["cell_type"].value_counts().to_string())
'''

STATS = re.compile(r"nhood_enrichment|co_occurrence|sq\.(gr|pl)\.ripley|centrality_scores")


def patch(nb):
    cells = nb["cells"]
    if any("cell_type_map" in "".join(c["source"]) for c in cells):
        print("already patched, nothing to do")
        return False

    anchor = next(
        i for i, c in enumerate(cells)
        if c["cell_type"] == "code" and "render_labels" in "".join(c["source"])
    )
    cells[anchor + 1: anchor + 1] = [
        cell("markdown", MD1), cell("code", CODE1),
        cell("markdown", MD2), cell("code", CODE2),
    ]

    for c in cells:
        if c["cell_type"] != "code":
            continue
        s = "".join(c["source"])
        if not STATS.search(s):
            continue
        s = s.replace('cluster_key="leiden"', 'cluster_key="cell_type"')
        s = s.replace(
            'adata.obs["leiden"].cat.categories[:3].tolist()',
            'adata.obs["cell_type"].cat.categories.tolist()',
        )
        # n_splits is deprecated in squidpy 1.8 and removed in 1.10
        s = s.replace(', n_splits=1)', ')')
        c["source"] = s.splitlines(keepends=True)
    return True


def main():
    if not NB.exists():
        sys.exit(f"{NB} not found — run from the repo root")
    import paths
    if not paths.DATA.exists():
        sys.exit(
            f"shared data dir {paths.DATA} not found.\n"
            "This script must run where the data is staged (the workshop server),\n"
            "or set PHYSALIA_DATA to a local copy."
        )

    backup = NB.with_suffix(".ipynb.bak")
    shutil.copy(NB, backup)
    print(f"backup -> {backup}")

    nb = json.load(open(NB))
    if patch(nb):
        json.dump(nb, open(NB, "w"), indent=1)
        print(f"patched -> {len(nb['cells'])} cells")
    else:
        print("already patched - executing anyway to regenerate outputs")

    import nbformat
    from nbclient import NotebookClient

    nbf = nbformat.read(NB, as_version=4)
    t = time.time()
    NotebookClient(
        nbf, timeout=1800, kernel_name="python3",
        resources={"metadata": {"path": str(NB.parent)}},
    ).execute()
    nbformat.write(nbf, NB)
    print(f"executed OK in {time.time() - t:.0f}s")
    print(f"if it looks right: rm {backup}")


if __name__ == "__main__":
    main()

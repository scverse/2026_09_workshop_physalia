#!/usr/bin/env python
"""One health check for the whole course.

Verifies the kernel, the libraries, the shared data and write access, then
prints a status block you can paste into Slack if something is wrong.

    pixi run check              # or: python scripts/healthcheck.py
    python scripts/healthcheck.py --fetch   # also download missing data

Downloading is opt-in on purpose. On the teaching server the data is staged
once and shared; if this script fetched on failure, thirty people hitting it at
once would saturate the box.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paths  # noqa: E402

EXPECTED = {
    "scanpy": "1.12", "anndata": "0.13", "squidpy": "1.8",
    "spatialdata": "0.8", "spatialdata_io": "0.7", "spatialdata_plot": "0.4",
    "scvi": "1.5", "sopa": "2.2", "cellcharter": "0.3", "liana": "1.10",
}

results: list[tuple[str, bool, str]] = []


def check(name):
    """Register a check. The function returns a detail string or raises."""
    def wrap(fn):
        try:
            results.append((name, True, fn() or "ok"))
        except Exception as exc:  # noqa: BLE001 - a failed check must not stop the rest
            detail = f"{type(exc).__name__}: {exc}"
            if os.environ.get("PHYSALIA_TRACE"):
                detail += "\n" + traceback.format_exc()
            results.append((name, False, detail))
        return fn
    return wrap


# 1. the single most common failure: the wrong kernel -----------------------
@check("kernel / interpreter")
def _kernel():
    exe = sys.executable
    if "physalia" not in exe and not os.environ.get("PHYSALIA_ANY_PYTHON"):
        raise RuntimeError(
            f"running {exe}, which is not the workshop environment.\n"
            "     In VS Code, top right of the notebook, pick "
            '"Physalia spatial omics".'
        )
    return f"{exe} (python {platform.python_version()})"


# 2. libraries present, and new enough --------------------------------------
@check("libraries")
def _libs():
    import importlib
    bad, seen = [], []
    for mod, want in EXPECTED.items():
        try:
            got = importlib.import_module(mod).__version__
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{mod}: not importable ({exc})")
            continue
        seen.append(f"{mod}=={got}")
        if not got.startswith(want):
            bad.append(f"{mod}: expected {want}.x, got {got}")
    if bad:
        raise RuntimeError("; ".join(bad))
    return " ".join(seen)


# 3. resolVI and gimVI specifically - the two that justify Day 3 -------------
@check("scvi.external RESOLVI + GIMVI")
def _scvi_external():
    from scvi.external import GIMVI, RESOLVI  # noqa: F401
    return "both importable"


# 4. shared data -------------------------------------------------------------
@check("shared data")
def _data():
    manifest_path = paths.REPO / "data_manifest.json"
    if not paths.DATA.exists():
        raise RuntimeError(
            f"{paths.DATA} does not exist.\n"
            "     On the course server this is staged for you - tell an instructor.\n"
            "     Running locally? python scripts/healthcheck.py --fetch"
        )
    if not manifest_path.exists():
        return f"{paths.DATA} present (no manifest yet)"
    manifest = json.loads(manifest_path.read_text())
    missing = [rel for rel in manifest["files"] if not (paths.DATA / rel).exists()]
    if missing:
        raise RuntimeError(
            f"{len(missing)} of {len(manifest['files'])} files missing under "
            f"{paths.DATA}: {', '.join(missing[:4])}"
            + (" ..." if len(missing) > 4 else "")
        )
    return f"{len(manifest['files'])} files present under {paths.DATA}"


# 5. write access to their own scratch space ---------------------------------
@check("write access")
def _write():
    probe = paths.OUT / ".probe"
    probe.write_text("ok")
    probe.unlink()
    return f"{paths.OUT} writable"


# 6. functional, not just importable -----------------------------------------
@check("functional: numerics + plotting")
def _numerics():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import torch
    t = torch.ones(8, 8) @ torch.ones(8, 8)
    assert float(t[0, 0]) == 8.0
    fig, ax = plt.subplots()
    ax.plot(np.arange(5))
    plt.close(fig)
    return f"torch {torch.__version__} (cuda={torch.cuda.is_available()}), matplotlib ok"


@check("functional: geometry / CRS")
def _geometry():
    import geopandas as gpd
    from shapely.geometry import Point
    g = gpd.GeoDataFrame(geometry=[Point(11.58, 48.14)], crs="EPSG:4326").to_crs(3857)
    assert round(g.geometry.iloc[0].x) == 1289080
    return "pyproj + geopandas transform correct"


@check("functional: spatial graph")
def _graph():
    import numpy as np
    import scanpy as sc
    import squidpy as sq
    rng = np.random.default_rng(0)
    ad = sc.AnnData(rng.poisson(1.0, (60, 12)).astype("float32"))
    ad.obsm["spatial"] = rng.random((60, 2))
    sq.gr.spatial_neighbors(ad, coord_type="generic", delaunay=True)
    n = int(ad.obsp["spatial_connectivities"].nnz)
    assert n > 0
    return f"squidpy built a Delaunay graph ({n} edges)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true",
                    help="download missing shared data (do NOT use on the course server)")
    args = ap.parse_args()

    if args.fetch or os.environ.get("PHYSALIA_ALLOW_DOWNLOAD"):
        print("--fetch given: run scripts/stage_data.sh to populate", paths.DATA)

    width = max(len(n) for n, _, _ in results)
    print("\n" + "=" * 64)
    print("  Physalia spatial omics - setup check")
    print("=" * 64)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<{width}}  {detail}")
    print("=" * 64)

    failed = [n for n, ok, _ in results if not ok]
    if failed:
        print(f"  {len(failed)} check(s) FAILED: {', '.join(failed)}")
        print("  Copy this whole block into the course Slack.")
        print("=" * 64 + "\n")
        return 1
    print("  SETUP OK - you are ready for the course.")
    print("=" * 64 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

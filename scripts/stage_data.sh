#!/usr/bin/env bash
# Populate the shared, read-only data directory. Instructor-run, once.
#
#   bash scripts/stage_data.sh            # the teaching set (~1 GB)
#   STAGE_FULL=1 bash scripts/stage_data.sh   # also the full 9.2 GB Rep1 slide
#
# Participants never run this. They read what it produces.
set -euo pipefail

DATA_DIR=${DATA_DIR:-/opt/workshop/data}
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=${PY:-$REPO/.pixi/envs/default/bin/python}
WORK="$DATA_DIR/.staging"

mkdir -p "$DATA_DIR" "$WORK"
say() { printf "\n=== %s ===\n" "$1"; }

# 10x public Xenium. The 2-FOV subset is the teaching spine: small enough that
# 25 people can each open it on a CPU box, real enough to show every artifact
# we want to talk about in the QC session.
SMALL_URL="https://cf.10xgenomics.com/samples/xenium/2.0.0/Xenium_V1_human_Breast_2fov/Xenium_V1_human_Breast_2fov_outs.zip"
FULL_URL="https://cf.10xgenomics.com/samples/xenium/1.0.1/Xenium_FFPE_Human_Breast_Cancer_Rep1/Xenium_FFPE_Human_Breast_Cancer_Rep1_outs.zip"

fetch_and_convert () {  # url, name
  local url=$1 name=$2
  if [ -d "$DATA_DIR/$name.zarr" ]; then
    echo "$name.zarr already present, skipping"; return
  fi
  say "downloading $name"
  curl -fL --retry 3 -o "$WORK/$name.zip" "$url"
  say "unzipping $name"
  rm -rf "$WORK/$name" && mkdir -p "$WORK/$name"
  unzip -q "$WORK/$name.zip" -d "$WORK/$name"
  # 10x bundles sometimes nest everything one level down
  local src="$WORK/$name"
  [ "$(ls -1 "$src" | wc -l)" -eq 1 ] && [ -d "$src/$(ls -1 "$src")" ] && src="$src/$(ls -1 "$src")"
  say "converting $name to zarr"
  "$PY" - "$src" "$DATA_DIR/$name.zarr" <<'PY'
import sys
import spatialdata_io
sdata = spatialdata_io.xenium(sys.argv[1])
sdata.write(sys.argv[2], overwrite=True)
print(sdata)
PY
  rm -rf "$WORK/$name" "$WORK/$name.zip"
}

fetch_and_convert "$SMALL_URL" "xenium_breast_2fov"
[ "${STAGE_FULL:-0}" = "1" ] && fetch_and_convert "$FULL_URL" "xenium_breast_rep1"

# Visium, for the grid-vs-point contrast in the spatial-graph session. Coming
# from squidpy rather than a URL so it stays pinned to the installed version.
say "visium H&E (squidpy)"
"$PY" - "$DATA_DIR" <<'PY'
import sys, pathlib
out = pathlib.Path(sys.argv[1]) / "visium_hne.zarr"
if out.exists():
    print("already present"); raise SystemExit
import squidpy as sq
sdata = sq.datasets.visium_hne_sdata()
sdata.write(out, overwrite=True)
print(sdata)
PY

say "manifest"
"$PY" - "$DATA_DIR" "$REPO/data_manifest.json" <<'PY'
import json, pathlib, sys
data, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
entries, total = [], 0
for p in sorted(data.iterdir()):
    if p.name.startswith("."):
        continue
    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
    entries.append(p.name); total += size
    print(f"  {p.name:<32} {size/2**30:6.2f} GB")
out.write_text(json.dumps({"files": entries, "total_bytes": total}, indent=2) + "\n")
print(f"\n  {len(entries)} entries, {total/2**30:.2f} GB -> {out}")
PY

rmdir "$WORK" 2>/dev/null || true
echo
echo "Staged into $DATA_DIR. Make it read-only with:"
echo "  sudo chmod -R a+rX,go-w $DATA_DIR"

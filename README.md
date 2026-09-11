# Spatial Omics Data Analysis: From Raw Data to AI Insights

Physalia course, **14–16 September 2026**, 14:00–18:00 Berlin time, online.
Instructors: Tim Treis, Robert Gutgesell (Helmholtz Munich).

---

## Participants: start here

You need **VS Code** and the **Remote-SSH** extension. Nothing else — no Python,
no conda, no pixi on your own machine.

1. **Connect.** VS Code → `Remote-SSH: Connect to Host` → the host Physalia sent you.
2. **Clone this repo** into your home directory:
   ```bash
   git clone https://github.com/scverse/2026_09_workshop_physalia.git
   cd 202609_workshop_physalia
   ```
3. **Open `notebooks/00_setup_check.ipynb`.**
4. **Pick the kernel.** Top right, choose **"Physalia spatial omics"**.
   It is already installed — you do not need to create an environment.
5. **Run All.** The last cell should print `SETUP OK`.

If anything fails, copy the whole status block into the course Slack. Please do
this **before day 1**, not on the morning of — that way we can fix it in time.

### Where things live

| | |
|---|---|
| Shared data | `/opt/workshop/data` — **read-only**, same for everyone |
| Your work | inside your own clone; `outputs/` is git-ignored |

Import `paths.py` rather than hardcoding either:

```python
import paths
sdata = spatialdata.read_zarr(paths.data("xenium_breast.zarr"))
fig.savefig(paths.OUT / "my_figure.png")
```

### Running it on your own machine later

Everything here is reproducible off the course server. Install
[pixi](https://pixi.sh), then:

```bash
pixi install                 # uses the committed lock, so you get our exact versions
export PHYSALIA_DATA=/where/you/put/the/data
pixi run check
```

`pixi.lock` covers linux-64, osx-arm64 and win-64.

---

## Instructors

```bash
sudo -v && bash scripts/bootstrap.sh     # full server setup, ~20 min, re-runnable
bash scripts/stage_data.sh               # data only
pixi run check                           # verify
```

`bootstrap.sh` installs pixi, builds the environment from the committed lock,
installs the kernelspec **system-wide** (`--prefix=/usr/local`, so it is visible
to every account including ones that do not exist yet), and stages the data.
Nothing is written into participant home directories, so the setup survives the
participant accounts being recreated.

### Environment notes

- `scvi-tools`, `squidpy` and `spatialdata-io` come from PyPI, not conda-forge:
  each feedstock lags PyPI by one patch and this course teaches the current stack.
- `cellpose` is pinned `<4`. Unpinned the solver picks 4.x on Linux and 3.0.9 on
  macOS, so a Mac-authored notebook breaks on the server. Worse, 4.x (Cellpose-SAM)
  removed the `models.Cellpose` class and dropped `cyto3`/`nuclei` from
  `MODEL_NAMES` — passing `cyto3` to v4 [silently falls back to
  `cpsam_v2`](https://github.com/MouseLand/cellpose/issues/1176) rather than
  erroring. It is also ~3× slower on CPU at fp32 and ~76× slower at its shipped
  `use_bfloat16=True` default, since bf16 is emulated on CPU.
- `napari` lives in the `local` feature only (`pixi install -e local`); it cannot
  render over Remote-SSH.

## Schedule

| Day | Sessions |
|---|---|
| 1 | Introduction to SpatialData · Quality control and segmentation (SOPA) · SpatialData + Squidpy |
| 2 | Spatial structure: clustering and niches · Cell–cell communication · Gene-level spatial analysis |
| 3 | Why AI in spatial omics · AI in practice: morphology and resolVI · Synthesis |

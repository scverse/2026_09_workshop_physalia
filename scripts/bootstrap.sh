#!/usr/bin/env bash
# Rebuild the whole server-side setup from nothing. Instructor-run, needs sudo.
#
#   sudo -v && bash scripts/bootstrap.sh
#
# Safe to re-run. If Carlo hands us a wiped machine on Monday morning, this is
# the recovery path: ~20 minutes, mostly unattended.
set -euo pipefail

WORKSHOP_ROOT=${WORKSHOP_ROOT:-/opt/workshop}
REPO_URL=${REPO_URL:-https://github.com/scverse/2026_09_workshop_physalia.git}
ENV_DIR="$WORKSHOP_ROOT/physalia"
DATA_DIR="$WORKSHOP_ROOT/data"

say() { printf "\n=== %s ===\n" "$1"; }

say "1/5 pixi"
if ! command -v pixi >/dev/null 2>&1; then
  curl -fsSL https://pixi.sh/install.sh | bash
fi
export PATH="$HOME/.pixi/bin:$PATH"
pixi --version

say "2/5 workshop tree"
sudo mkdir -p "$WORKSHOP_ROOT" "$DATA_DIR"
sudo chown "$USER":"$USER" "$WORKSHOP_ROOT" "$DATA_DIR"
if [ -d "$ENV_DIR/.git" ]; then
  git -C "$ENV_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$ENV_DIR"
fi

say "3/5 environment (from the committed lock - no solving)"
cd "$ENV_DIR"
pixi install -e default --frozen
PY="$ENV_DIR/.pixi/envs/default/bin/python"
"$PY" -c "import scanpy, spatialdata, squidpy, sopa; from scvi.external import RESOLVI; print('imports ok')"

say "4/5 system-wide kernelspec"
# --prefix=/usr/local puts it on Jupyter's SYSTEM search path, so every account
# sees it - including accounts that do not exist yet. Nothing is written into
# any home directory, so this survives Carlo recreating the participant users.
sudo "$PY" -m ipykernel install --prefix=/usr/local \
     --name physalia --display-name "Physalia spatial omics"
sudo chmod -R a+rX /usr/local/share/jupyter "$WORKSHOP_ROOT"

say "5/5 data"
if [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
  bash "$ENV_DIR/scripts/stage_data.sh"
else
  echo "data dir already populated, skipping (delete $DATA_DIR to force)"
fi
# read-only to everyone but us: participants read from here, write in their clone
sudo chmod -R a+rX,go-w "$DATA_DIR"

say "verify"
"$PY" "$ENV_DIR/scripts/healthcheck.py" || true
cat <<EOF

Done. Participants now need only:
  git clone $REPO_URL
  open a notebook, pick the "Physalia spatial omics" kernel

Shared data : $DATA_DIR  (read-only)
Environment : $ENV_DIR
Kernelspec  : /usr/local/share/jupyter/kernels/physalia
EOF

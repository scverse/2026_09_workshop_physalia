#!/usr/bin/env bash
# Pre-install the Python and Jupyter extensions into every participant's
# VS Code server, so nobody is prompted to install anything.
#
#   bash scripts/seed_vscode_extensions.sh
#
# Remote-SSH runs extensions ON THE SERVER, not on the participant's laptop.
# Without this, every participant is prompted to install Python + Jupyter the
# first time they open a notebook, then waits while ~300 MB downloads - 25 times
# over, at the start of day 1. Seeding also means an offline or slow client
# still gets a working notebook.
#
# Only the extensions directory is seeded, never the server binary: that is keyed
# to the client's VS Code commit and differs per participant, so it must be left
# for VS Code to fetch.
set -uo pipefail

SRC=${SRC:-/opt/workshop/vscode-extensions}
N=${N:-30}

[ -d "$SRC" ] || { echo "no reference extension set at $SRC" >&2; exit 1; }

for i in $(seq 1 "$N"); do
  u=user$i; h=/home/$u
  id "$u" >/dev/null 2>&1 || continue
  d="$h/.vscode-server/extensions"
  sudo -u "$u" mkdir -p "$d" 2>/dev/null || { echo "  $u: cannot create $d"; continue; }
  n=0
  for e in "$SRC"/*; do
    b=$(basename "$e")
    sudo test -e "$d/$b" && continue
    sudo cp -a "$e" "$d/$b" && n=$((n+1))
  done
  sudo chown -R "$u":"$u" "$h/.vscode-server"
  echo "  $u: $n extension(s) added"
done

cat <<'EOF'

Seeded. VS Code rebuilds extensions.json from the directory on connect, so
participants get Python + Jupyter with no prompt and no download.
EOF

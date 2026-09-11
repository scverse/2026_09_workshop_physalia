#!/usr/bin/env bash
# Reset a participant account to the state they will see on day 1.
# Instructor-run, needs sudo.
#
#   bash scripts/reset_user.sh user1 --dry-run   # show what would happen
#   bash scripts/reset_user.sh user1             # do it
#   bash scripts/reset_user.sh --all             # every participant account
#
# KEEPS  .ssh  - their login lives there, removing it locks them out.
# WIPES  everything else in the home, including files they created.
# LEAVES the home as: .ssh + /etc/skel dotfiles + a fresh clone of the workshop.
#
# This exists so we can test the real participant experience repeatedly rather
# than guessing at it. It is destructive by design - there is no undo.
set -uo pipefail

REPO_URL=${REPO_URL:-https://github.com/scverse/2026_09_workshop_physalia.git}
REPO_NAME=2026_09_workshop_physalia
KEEP=(.ssh)
N=${N:-30}

DRY=0; TARGETS=()
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --all)     for i in $(seq 1 "$N"); do TARGETS+=("user$i"); done ;;
    -*)        echo "unknown flag: $a" >&2; exit 2 ;;
    *)         TARGETS+=("$a") ;;
  esac
done
[ ${#TARGETS[@]} -eq 0 ] && { echo "usage: $0 <user> [<user>...] | --all  [--dry-run]" >&2; exit 2; }

run() { if [ "$DRY" = "1" ]; then echo "      $*"; else eval "$@"; fi; }

for u in "${TARGETS[@]}"; do
  h="/home/$u"
  if ! id "$u" >/dev/null 2>&1 || [ ! -d "$h" ]; then
    echo "  $u: no such account, skipping"; continue
  fi
  echo "  $u:"
  # sudo for the listing too - homes are 700, so even ubuntu cannot read them
  for e in $(sudo ls -A "$h" 2>/dev/null); do
    skip=0; for k in "${KEEP[@]}"; do [ "$e" = "$k" ] && skip=1; done
    [ "$skip" = "1" ] && { echo "      keep    $e"; continue; }
    run "sudo rm -rf '$h/$e'"
    echo "      remove  $e"
  done
  for f in .bashrc .profile .bash_logout; do
    run "sudo install -o '$u' -g '$u' -m 644 /etc/skel/$f '$h/$f'"
  done
  echo "      restore .bashrc .profile .bash_logout from /etc/skel"
  run "sudo -u '$u' git clone -q '$REPO_URL' '$h/$REPO_NAME'"
  echo "      clone   $REPO_NAME"
  run "sudo chmod 700 '$h'"
  run "sudo chown '$u':'$u' '$h'"
  echo "      chmod   700 (private to them)"
done

[ "$DRY" = "1" ] && echo && echo "(dry run - nothing changed)"
exit 0

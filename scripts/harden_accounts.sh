#!/usr/bin/env bash
# Make participant accounts private and pre-seed the workshop folder.
# Instructor-run, needs sudo, safe to re-run.
#
# Why private homes: every account is in the `sharedusers` group and homes ship
# as drwxr-x---, so by default any participant can read any other participant's
# work. We invite people to bring their own datasets for the day-3 session, and
# some of them work in industry - that data must not be readable by 29 strangers.
# Instructors keep access through sudo, so nothing we need breaks.
set -uo pipefail

REPO_URL=${REPO_URL:-https://github.com/scverse/2026_09_workshop_physalia.git}
REPO_NAME=2026_09_workshop_physalia
N=${N:-30}

for i in $(seq 1 "$N"); do
  u=user$i; h=/home/$u
  [ -d "$h" ] || continue
  sudo chmod 700 "$h"
  # sudo test, not plain test: homes are 700, so even ubuntu cannot stat inside
  # them. Without sudo this check silently reports "missing" and the clone below
  # fails with "destination path already exists".
  if sudo test -d "$h/$REPO_NAME"; then
    sudo -u "$u" git -C "$h/$REPO_NAME" pull -q --ff-only 2>/dev/null \
      && echo "  $u: updated" || echo "  $u: pull skipped (local changes)"
  else
    sudo -u "$u" git clone -q "$REPO_URL" "$h/$REPO_NAME" && echo "  $u: cloned"
  fi
done

# The previous course's archived material is root-only. Moving it out of /home
# stripped the protection its home directories used to provide.
[ -d /opt/_archive ] && { sudo chown -R root:root /opt/_archive; sudo chmod 700 /opt/_archive; echo "  /opt/_archive locked to root"; }

echo "done: $N homes private, repo present in each"

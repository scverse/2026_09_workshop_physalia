"""Where things live. Import this instead of hardcoding paths in notebooks."""
from __future__ import annotations
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent

# Read-only, shared by all participants, staged by the instructors.
# Override with PHYSALIA_DATA to run these notebooks on your own machine.
DATA = Path(os.environ.get("PHYSALIA_DATA", "/opt/workshop/data"))

# Your own scratch space, inside your clone. Never shared, never overwritten.
OUT = Path(os.environ.get("PHYSALIA_OUT", REPO / "outputs"))
OUT.mkdir(parents=True, exist_ok=True)


def data(*parts: str) -> Path:
    """Resolve a path under the shared data directory, failing loudly if absent."""
    p = DATA.joinpath(*parts)
    if not p.exists():
        raise FileNotFoundError(
            f"{p} not found.\n"
            f"Shared data dir is {DATA} (set PHYSALIA_DATA to change it).\n"
            f"Run `pixi run check` to diagnose."
        )
    return p

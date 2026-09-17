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


def precomputed(*parts: str) -> Path | None:
    """Find a precomputed artifact (scVI latents, cell type cache, ...).

    Checks the shared, read-only cache under DATA/precomputed first (staged by the
    instructors, the same file for every participant), then your own OUT in case you
    computed it yourself earlier. Returns None if neither has it, so the caller can
    recompute inline.
    """
    shared = DATA / "precomputed" / Path(*parts)
    if shared.exists():
        return shared
    own = OUT.joinpath(*parts)
    if own.exists():
        return own
    return None

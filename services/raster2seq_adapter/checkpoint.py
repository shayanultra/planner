"""Resolve local Raster2Seq checkpoint paths and config (no HF download when local)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.raster2seq_adapter.errors import CheckpointNotFoundError

# Primary Slice A checkpoint (goal.md / Session 2–3 docs)
CUBICASA5K_ALIAS = "cubicasa5k"
CUBICASA5K_EXPECTED_BYTES = 1_452_141_664
DEFAULT_REPO = "haopt/Raster2Seq"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CKPT = (
    _REPO_ROOT / "Raster2Seq" / "checkpoints" / "cubicasa5k" / "checkpoint.pth"
)


def default_checkpoint_path(alias: str = CUBICASA5K_ALIAS) -> Path:
    if alias not in (CUBICASA5K_ALIAS, "cc5k", "cubicasa"):
        raise CheckpointNotFoundError(
            f"Unsupported checkpoint alias '{alias}'. Slice A primary is '{CUBICASA5K_ALIAS}'."
        )
    return _DEFAULT_CKPT


def resolve_local_checkpoint(
    alias: str = CUBICASA5K_ALIAS,
    *,
    path: str | Path | None = None,
    expected_bytes: int | None = CUBICASA5K_EXPECTED_BYTES,
) -> Path:
    """Return absolute path to an on-disk checkpoint; verify size when expected_bytes set."""
    ckpt = Path(path) if path is not None else default_checkpoint_path(alias)
    ckpt = ckpt.expanduser().resolve()
    if not ckpt.is_file():
        raise CheckpointNotFoundError(
            f"Checkpoint not found at {ckpt}. "
            f"Download cubicasa5k per docs/session/2026-08-01-raster2seq-checkpoint.md"
        )
    if expected_bytes is not None:
        size = ckpt.stat().st_size
        if size != expected_bytes:
            raise CheckpointNotFoundError(
                f"Checkpoint size mismatch at {ckpt}: got {size} bytes, "
                f"expected {expected_bytes} (cubicasa5k)."
            )
    return ckpt


def load_local_config(checkpoint_path: Path) -> dict[str, Any]:
    """Load sibling config.json next to checkpoint.pth."""
    cfg_path = checkpoint_path.parent / "config.json"
    if not cfg_path.is_file():
        raise CheckpointNotFoundError(f"Missing config.json next to checkpoint: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

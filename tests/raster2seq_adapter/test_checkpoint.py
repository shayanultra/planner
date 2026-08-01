"""Checkpoint resolution tests."""

from pathlib import Path

import pytest

from services.raster2seq_adapter import (
    CUBICASA5K_EXPECTED_BYTES,
    CheckpointNotFoundError,
    resolve_local_checkpoint,
)
from services.raster2seq_adapter.checkpoint import load_local_config


def test_resolve_local_cubicasa5k_on_disk() -> None:
    path = resolve_local_checkpoint("cubicasa5k")
    assert path.is_file()
    assert path.stat().st_size == CUBICASA5K_EXPECTED_BYTES
    cfg = load_local_config(path)
    assert cfg.get("checkpoint_key") == "cubicasa5k"
    assert "inference_args" in cfg


def test_missing_checkpoint_raises(tmp_path: Path) -> None:
    with pytest.raises(CheckpointNotFoundError, match="not found"):
        resolve_local_checkpoint("cubicasa5k", path=tmp_path / "nope.pth", expected_bytes=None)


def test_wrong_size_raises(tmp_path: Path) -> None:
    bad = tmp_path / "checkpoint.pth"
    bad.write_bytes(b"tiny")
    with pytest.raises(CheckpointNotFoundError, match="size mismatch"):
        resolve_local_checkpoint("cubicasa5k", path=bad, expected_bytes=CUBICASA5K_EXPECTED_BYTES)

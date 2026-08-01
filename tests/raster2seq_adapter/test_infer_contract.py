"""Contract tests for infer_polygons (mocked generate — no full model required)."""

from pathlib import Path

import numpy as np
import pytest

from services.floorplan_input import NormalizedRaster
from services.raster2seq_adapter import (
    CheckpointNotFoundError,
    infer_polygons,
)


def _fake_raster() -> NormalizedRaster:
    rgb = np.zeros((32, 32, 3), dtype=np.uint8)
    rgb[0, 0] = (255, 0, 0)
    return NormalizedRaster(
        rgb=rgb,
        source_kind="image",
        content_sha256="a" * 64,
        page=1,
        width=32,
        height=32,
    )


def test_infer_records_checkpoint_metadata() -> None:
    def fake_generate(_rgb):
        poly = np.array([[1, 1], [5, 1], [5, 5], [1, 5]], dtype=float)
        return {"room": [[poly]], "labels": [[3]]}

    result = infer_polygons(_fake_raster(), _generate_fn=fake_generate)
    assert result.checkpoint_alias == "cubicasa5k"
    assert result.checkpoint_repo == "haopt/Raster2Seq"
    assert Path(result.checkpoint_path).name == "checkpoint.pth"
    assert Path(result.checkpoint_path).is_file()
    assert result.source_content_sha256 == "a" * 64
    assert result.polish_applied is False
    assert len(result.polygons) == 1
    assert result.polygons[0].kind == "room"


def test_infer_polish_toggle() -> None:
    dense = np.array(
        [[0, 0], [5, 0], [10, 0], [10, 10], [0, 10], [0, 0]], dtype=float
    )

    def fake_generate(_rgb):
        return {"room": [[dense]], "labels": [[3]]}

    raw = infer_polygons(_fake_raster(), polish=False, _generate_fn=fake_generate)
    polished = infer_polygons(
        _fake_raster(), polish=True, polish_tolerance=1.0, _generate_fn=fake_generate
    )
    assert raw.polish_applied is False
    assert polished.polish_applied is True
    assert len(polished.polygons[0].points) <= len(raw.polygons[0].points)


def test_infer_missing_checkpoint_path(tmp_path: Path) -> None:
    with pytest.raises(CheckpointNotFoundError):
        infer_polygons(
            _fake_raster(),
            checkpoint_path=tmp_path / "missing.pth",
            _generate_fn=lambda r: {"room": [[]], "labels": [[]]},
        )


def test_adapter_has_no_grok_cosmos_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "services" / "raster2seq_adapter"
    banned = (
        "from grok",
        "import grok",
        "open_webui",
        "ChatCompletion",
        "openai",
        "cosmos_generate",
    )
    for py in root.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        lower = text.lower()
        for token in banned:
            assert token.lower() not in lower, f"{py.name} contains banned token {token}"

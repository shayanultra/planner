"""Fixtures for parse_and_map seam tests (no live Raster2Seq)."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.floorplan_input import NormalizedRaster
from services.raster2seq_adapter.infer import PolygonSequenceResult
from services.raster2seq_adapter.map_output import PolygonItem

REPO = Path(__file__).resolve().parents[2]
FIXTURE_PNG = REPO / "tests" / "fixtures" / "floorplan_tiny.png"


@pytest.fixture
def fixture_png() -> Path:
    assert FIXTURE_PNG.is_file(), f"missing fixture {FIXTURE_PNG}"
    return FIXTURE_PNG


@pytest.fixture
def canned_polygons() -> list[PolygonItem]:
    return [
        PolygonItem(
            id="p0",
            label="kitchen",
            kind="room",
            points=[[0.0, 0.0], [10.0, 0.0], [10.0, 8.0], [0.0, 8.0]],
        ),
        PolygonItem(
            id="p1",
            label="door",
            kind="door",
            points=[[10.0, 3.0], [10.0, 5.0]],
        ),
    ]


@pytest.fixture
def mock_infer(canned_polygons: list[PolygonItem]):
    def _infer(
        normalized: NormalizedRaster,
        *,
        polish: bool = False,
        polish_tolerance: float = 1.0,
        **_kwargs,
    ) -> PolygonSequenceResult:
        return PolygonSequenceResult(
            polygons=list(canned_polygons),
            checkpoint_alias="cubicasa5k",
            checkpoint_path="Raster2Seq/checkpoints/cubicasa5k/checkpoint.pth",
            checkpoint_repo="haopt/Raster2Seq",
            image_size=256,
            polish_applied=polish,
            source_content_sha256=normalized.content_sha256,
        )

    return _infer


def db_available() -> bool:
    try:
        from services.layout_builder import connect

        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:  # noqa: BLE001
        return False

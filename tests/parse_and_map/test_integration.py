"""Live Raster2Seq E2E — skip when runtime/ops unavailable (Mac detectron2 gap)."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.layout_builder import connect
from services.parse_and_map import parse_and_map_floorplan
from tests.parse_and_map.conftest import db_available


def _raster2seq_runtime_ok() -> bool:
    try:
        import detectron2  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    try:
        from services.raster2seq_adapter.checkpoint import resolve_local_checkpoint

        resolve_local_checkpoint("cubicasa5k")
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not db_available(), reason="planner_ai Postgres not reachable"),
    pytest.mark.skipif(
        not _raster2seq_runtime_ok(),
        reason="Raster2Seq runtime missing (detectron2/ops); see docs/session/2026-08-01-raster2seq-mac-runtime.md",
    ),
]


def test_live_infer_end_to_end(fixture_png: Path) -> None:
    with connect() as conn:
        row = parse_and_map_floorplan(fixture_png, conn=conn, close_conn=False)
        assert row.id is not None
        assert row.svg
        assert row.geometry.get("polygons") is not None

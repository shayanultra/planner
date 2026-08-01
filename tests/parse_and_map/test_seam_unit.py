"""Unit tests for parse_and_map_floorplan with injected infer (no detectron2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.layout_builder import AUDIT_ACTION, connect
from services.parse_and_map import ParseAndMapError, parse_and_map_floorplan
from tests.parse_and_map.conftest import db_available

pytestmark = pytest.mark.skipif(not db_available(), reason="planner_ai Postgres not reachable")


def test_seam_with_mock_infer_persists_layout_svg_extrusion_audit(
    fixture_png: Path, mock_infer
) -> None:
    with connect() as conn:
        row = parse_and_map_floorplan(
            fixture_png,
            conn=conn,
            infer_fn=mock_infer,
            scale_meters_per_unit=0.05,
            close_conn=False,
        )
        assert row.id is not None
        assert row.geometry_fingerprint
        assert row.source_kind == "image"
        assert row.svg and "<svg" in row.svg
        assert row.extrusion["nodes"]
        # footprints only from 2D
        assert all("footprint" in n for n in row.extrusion["nodes"])
        assert len(row.geometry["polygons"]) == 2
        assert row.geometry["scale"]["meters_per_unit"] == 0.05

        with conn.cursor() as cur:
            cur.execute(
                "SELECT svg, geometry, extrusion FROM layouts WHERE id = %s",
                (row.id,),
            )
            svg, geometry, extrusion = cur.fetchone()
            assert "<svg" in svg
            geom = geometry if isinstance(geometry, dict) else json.loads(geometry)
            assert geom["schema_version"] == "1"
            ext = extrusion if isinstance(extrusion, dict) else json.loads(extrusion)
            assert ext["wall_height_m"] == 2.7

            cur.execute(
                "SELECT action, success FROM audit_log WHERE layout_id = %s ORDER BY id DESC LIMIT 1",
                (row.id,),
            )
            action, success = cur.fetchone()
            assert action == AUDIT_ACTION
            assert success is True


def test_missing_input_raises(tmp_path: Path, mock_infer) -> None:
    with pytest.raises(ParseAndMapError, match="not found"):
        parse_and_map_floorplan(tmp_path / "nope.png", infer_fn=mock_infer)


def test_no_catalog_or_optimizer_imports() -> None:
    """Ticket 06 must not introduce catalog/optimizer paths."""
    import services.parse_and_map.seam as seam_mod

    src = Path(seam_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("optimize_kitchen", "cabinets", "finishes", "cosmos", "grok")
    lower = src.lower()
    for token in forbidden:
        assert token not in lower, f"forbidden token in seam: {token}"

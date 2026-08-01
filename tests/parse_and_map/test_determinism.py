"""Determinism: identical canned inputs → identical geometry_fingerprint."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.layout_builder import connect
from services.parse_and_map import parse_and_map_floorplan
from tests.parse_and_map.conftest import db_available

pytestmark = pytest.mark.skipif(not db_available(), reason="planner_ai Postgres not reachable")


def test_double_run_same_fingerprint(fixture_png: Path, mock_infer) -> None:
    with connect() as conn:
        a = parse_and_map_floorplan(
            fixture_png,
            conn=conn,
            infer_fn=mock_infer,
            scale_meters_per_unit=0.01,
            close_conn=False,
        )
        b = parse_and_map_floorplan(
            fixture_png,
            conn=conn,
            infer_fn=mock_infer,
            scale_meters_per_unit=0.01,
            close_conn=False,
        )
        # Distinct layout rows, identical geometry
        assert a.id != b.id
        assert a.geometry_fingerprint == b.geometry_fingerprint
        assert a.svg == b.svg
        assert a.extrusion == b.extrusion
        assert a.geometry["polygons"] == b.geometry["polygons"]

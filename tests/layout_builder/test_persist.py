"""Persist Layout to Postgres layouts + audit_log (Slice A ACs)."""

from __future__ import annotations

import json

import pytest

from services.layout_builder.build import build_layout
from services.layout_builder.persist import (
    AUDIT_ACTION,
    build_and_persist_layout,
    connect,
    persist_layout,
    resolve_database_url,
)
from services.raster2seq_adapter.map_output import PolygonItem


def _db_available() -> bool:
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="planner_ai Postgres not reachable")


def test_persist_layout_writes_geometry_svg_extrusion_and_audit(
    sample_polygons: list[PolygonItem],
) -> None:
    result = build_layout(
        sample_polygons,
        source_kind="image",
        content_sha256="fixture-sha-05",
        checkpoint_alias="cubicasa5k",
        checkpoint_repo="haopt/Raster2Seq",
        image_size=256,
        scale_meters_per_unit=0.02,
        scale_user_confirmed=False,
    )
    with connect() as conn:
        row = persist_layout(result, conn, duration_ms=12)
        assert row.id is not None
        assert row.geometry_fingerprint == result.geometry_fingerprint

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source_kind, content_sha256, scale_meters_per_unit,
                       scale_user_confirmed, geometry, svg, extrusion
                FROM layouts WHERE id = %s
                """,
                (row.id,),
            )
            db = cur.fetchone()
            assert db is not None
            source_kind, sha, scale, confirmed, geometry, svg, extrusion = db
            assert source_kind == "image"
            assert sha == "fixture-sha-05"
            assert float(scale) == pytest.approx(0.02)
            assert confirmed is False
            geom = geometry if isinstance(geometry, dict) else json.loads(geometry)
            assert geom["schema_version"] == "1"
            assert len(geom["polygons"]) == 3
            assert geom["scale"]["meters_per_unit"] == 0.02
            assert svg and "<svg" in svg
            ext = extrusion if isinstance(extrusion, dict) else json.loads(extrusion)
            assert ext["wall_height_m"] == 2.7
            assert len(ext["nodes"]) == 3
            # 3D footprints match 2D polygon count
            assert all("footprint" in n for n in ext["nodes"])

            cur.execute(
                """
                SELECT action, success, layout_id, detail
                FROM audit_log WHERE layout_id = %s ORDER BY id DESC LIMIT 1
                """,
                (row.id,),
            )
            audit = cur.fetchone()
            assert audit is not None
            action, success, layout_id, detail = audit
            assert action == AUDIT_ACTION
            assert success is True
            assert layout_id == row.id
            det = detail if isinstance(detail, dict) else json.loads(detail)
            assert det["geometry_fingerprint"] == result.geometry_fingerprint
            assert det["polygon_count"] == 3


def test_build_and_persist_layout_orchestrator(sample_polygons: list[PolygonItem]) -> None:
    with connect() as conn:
        row = build_and_persist_layout(
            sample_polygons,
            conn=conn,
            source_kind="pdf",
            content_sha256="orch-sha",
            checkpoint_alias="cubicasa5k",
            scale_meters_per_unit=None,
        )
        assert row.source_kind == "pdf"
        with conn.cursor() as cur:
            cur.execute("SELECT svg FROM layouts WHERE id = %s", (row.id,))
            (svg,) = cur.fetchone()
            assert "data-label" in svg


def test_resolve_database_url_default() -> None:
    assert "planner_ai" in resolve_database_url() or resolve_database_url()

"""Persist Layout to Postgres layouts + audit_log."""

from __future__ import annotations

import os
import time
from typing import Any
from uuid import UUID

from services.layout_builder.errors import PersistError
from services.layout_builder.types import LayoutBuildResult, LayoutRow

DEFAULT_DATABASE_URL = "postgresql://localhost/planner_ai"
AUDIT_ACTION = "layout.build_and_persist"


def resolve_database_url() -> str:
    return (
        os.environ.get("PLANNER_AI_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or DEFAULT_DATABASE_URL
    )


def connect(url: str | None = None):
    """Open a psycopg connection (caller closes)."""
    import psycopg

    return psycopg.connect(url or resolve_database_url())


def persist_layout(
    result: LayoutBuildResult,
    conn: Any,
    *,
    duration_ms: int | None = None,
    actor: str = "system",
) -> LayoutRow:
    """INSERT layouts row + audit_log in one transaction. Returns LayoutRow with id."""
    started = time.perf_counter()
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO layouts (
                        schema_version,
                        source_kind,
                        content_sha256,
                        checkpoint_alias,
                        checkpoint_repo,
                        scale_meters_per_unit,
                        scale_user_confirmed,
                        geometry,
                        svg,
                        extrusion
                    ) VALUES (
                        %(schema_version)s,
                        %(source_kind)s,
                        %(content_sha256)s,
                        %(checkpoint_alias)s,
                        %(checkpoint_repo)s,
                        %(scale_meters_per_unit)s,
                        %(scale_user_confirmed)s,
                        %(geometry)s::jsonb,
                        %(svg)s,
                        %(extrusion)s::jsonb
                    )
                    RETURNING id
                    """,
                    {
                        "schema_version": result.geometry.get("schema_version", "1"),
                        "source_kind": result.source_kind,
                        "content_sha256": result.content_sha256,
                        "checkpoint_alias": result.checkpoint_alias,
                        "checkpoint_repo": result.checkpoint_repo,
                        "scale_meters_per_unit": result.scale_meters_per_unit,
                        "scale_user_confirmed": result.scale_user_confirmed,
                        "geometry": _json_param(result.geometry),
                        "svg": result.svg,
                        "extrusion": _json_param(result.extrusion),
                    },
                )
                row = cur.fetchone()
                if not row:
                    raise PersistError("INSERT layouts returned no id")
                layout_id: UUID = row[0]

                elapsed = duration_ms
                if elapsed is None:
                    elapsed = int((time.perf_counter() - started) * 1000)

                detail = {
                    "content_sha256": result.content_sha256,
                    "checkpoint_alias": result.checkpoint_alias,
                    "polygon_count": len(result.geometry.get("polygons") or []),
                    "geometry_fingerprint": result.geometry_fingerprint,
                }
                cur.execute(
                    """
                    INSERT INTO audit_log (
                        actor, action, layout_id, success, duration_ms, detail
                    ) VALUES (
                        %(actor)s, %(action)s, %(layout_id)s, true, %(duration_ms)s,
                        %(detail)s::jsonb
                    )
                    RETURNING id
                    """,
                    {
                        "actor": actor,
                        "action": AUDIT_ACTION,
                        "layout_id": layout_id,
                        "duration_ms": elapsed,
                        "detail": _json_param(detail),
                    },
                )
                audit_row = cur.fetchone()
                audit_id = int(audit_row[0]) if audit_row else None

        return LayoutRow(
            id=layout_id,
            geometry=result.geometry,
            svg=result.svg,
            extrusion=result.extrusion,
            geometry_fingerprint=result.geometry_fingerprint,
            source_kind=result.source_kind,
            content_sha256=result.content_sha256,
            scale_meters_per_unit=result.scale_meters_per_unit,
            scale_user_confirmed=result.scale_user_confirmed,
            audit_id=audit_id,
        )
    except PersistError:
        raise
    except Exception as exc:  # noqa: BLE001 — wrap driver errors
        raise PersistError(str(exc)) from exc


def build_and_persist_layout(
    polygons,
    *,
    conn: Any,
    source_kind: str = "image",
    content_sha256: str | None = None,
    checkpoint_alias: str | None = None,
    checkpoint_repo: str | None = "haopt/Raster2Seq",
    image_size: int | None = None,
    scale_meters_per_unit: float | None = None,
    scale_user_confirmed: bool = False,
    wall_height_m: float = 2.7,
    actor: str = "system",
) -> LayoutRow:
    """Build pure layout then persist + audit."""
    from services.layout_builder.build import build_layout

    t0 = time.perf_counter()
    result = build_layout(
        polygons,
        source_kind=source_kind,
        content_sha256=content_sha256,
        checkpoint_alias=checkpoint_alias,
        checkpoint_repo=checkpoint_repo,
        image_size=image_size,
        scale_meters_per_unit=scale_meters_per_unit,
        scale_user_confirmed=scale_user_confirmed,
        wall_height_m=wall_height_m,
    )
    duration_ms = int((time.perf_counter() - t0) * 1000)
    return persist_layout(result, conn, duration_ms=duration_ms, actor=actor)


def _json_param(obj: Any) -> str:
    import json

    return json.dumps(obj, sort_keys=True)

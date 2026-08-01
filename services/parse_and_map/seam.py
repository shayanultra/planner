"""Public Reconstruction Path seam: normalize → Raster2Seq → layout persist."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from services.floorplan_input import normalize_floorplan_input
from services.layout_builder import LayoutRow, build_and_persist_layout, connect
from services.layout_builder.extrusion import DEFAULT_WALL_HEIGHT_M
from services.parse_and_map.errors import ParseAndMapError
from services.raster2seq_adapter.infer import PolygonSequenceResult

InferFn = Callable[..., PolygonSequenceResult]


def parse_and_map_floorplan(
    input_path: str | Path,
    *,
    conn: Any | None = None,
    infer_fn: InferFn | None = None,
    polish: bool = False,
    polish_tolerance: float = 1.0,
    scale_meters_per_unit: float | None = None,
    scale_user_confirmed: bool = False,
    wall_height_m: float = DEFAULT_WALL_HEIGHT_M,
    source_kind: str | None = None,
    close_conn: bool | None = None,
) -> LayoutRow:
    """Run full Reconstruction Path and persist Layout + audit_log.

    Parameters
    ----------
    input_path:
        Image or PDF path (ticket 03 normalize).
    conn:
        Open psycopg connection. If None, opens via ``layout_builder.connect``
        and closes when this call returns (unless ``close_conn=False``).
    infer_fn:
        Optional injectable geometry producer. Default is
        ``services.raster2seq_adapter.infer_polygons``. Unit tests inject a
        pure function returning canned ``PolygonSequenceResult`` so detectron2
        is not required.
    polish:
        Douglas-Peucker post-only polish (default off); forwarded to infer.
    """
    path = Path(input_path)
    if not path.is_file():
        raise ParseAndMapError(f"input not found: {path}")

    owns_conn = conn is None
    if owns_conn:
        conn = connect()
    if close_conn is None:
        close_conn = owns_conn

    try:
        normalized = normalize_floorplan_input(path)
        kind = source_kind or normalized.source_kind

        if infer_fn is None:
            from services.raster2seq_adapter import infer_polygons

            poly_result = infer_polygons(
                normalized,
                polish=polish,
                polish_tolerance=polish_tolerance,
            )
        else:
            poly_result = infer_fn(
                normalized,
                polish=polish,
                polish_tolerance=polish_tolerance,
            )

        if not isinstance(poly_result, PolygonSequenceResult):
            raise ParseAndMapError(
                f"infer_fn must return PolygonSequenceResult, got {type(poly_result)!r}"
            )
        if not poly_result.polygons:
            raise ParseAndMapError("infer produced empty polygon sequence")

        return build_and_persist_layout(
            poly_result,
            conn=conn,
            source_kind=kind,
            content_sha256=poly_result.source_content_sha256 or normalized.content_sha256,
            checkpoint_alias=poly_result.checkpoint_alias,
            checkpoint_repo=poly_result.checkpoint_repo,
            image_size=poly_result.image_size,
            scale_meters_per_unit=scale_meters_per_unit,
            scale_user_confirmed=scale_user_confirmed,
            wall_height_m=wall_height_m,
        )
    finally:
        if close_conn and conn is not None:
            conn.close()

"""Orchestrate pure layout build from Polygon Sequence (ticket 05)."""

from __future__ import annotations

from typing import Sequence

from services.layout_builder.canonicalize import geometry_fingerprint
from services.layout_builder.errors import LayoutBuilderError
from services.layout_builder.extrusion import DEFAULT_WALL_HEIGHT_M, polygons_to_extrusion
from services.layout_builder.geometry import polygons_to_geometry
from services.layout_builder.svg import polygons_to_svg
from services.layout_builder.types import LayoutBuildResult
from services.raster2seq_adapter.infer import PolygonSequenceResult
from services.raster2seq_adapter.map_output import PolygonItem


def _as_items(
    polygons: Sequence[PolygonItem] | PolygonSequenceResult,
) -> tuple[list[PolygonItem], dict]:
    if isinstance(polygons, PolygonSequenceResult):
        meta = {
            "content_sha256": polygons.source_content_sha256,
            "checkpoint_alias": polygons.checkpoint_alias,
            "checkpoint_repo": polygons.checkpoint_repo,
            "image_size": polygons.image_size,
        }
        return list(polygons.polygons), meta
    return list(polygons), {}


def build_layout(
    polygons: Sequence[PolygonItem] | PolygonSequenceResult,
    *,
    source_kind: str = "image",
    content_sha256: str | None = None,
    checkpoint_alias: str | None = None,
    checkpoint_repo: str | None = "haopt/Raster2Seq",
    image_size: int | None = None,
    scale_meters_per_unit: float | None = None,
    scale_user_confirmed: bool = False,
    wall_height_m: float = DEFAULT_WALL_HEIGHT_M,
) -> LayoutBuildResult:
    """Pure: polygons → Layout JSON + SVG + extrusion + fingerprint.

    Does not call Raster2Seq; consumes ticket-04 PolygonItem / PolygonSequenceResult only.
    """
    items, meta = _as_items(polygons)
    if not items:
        raise LayoutBuilderError("empty polygon sequence")

    sha = content_sha256 if content_sha256 is not None else meta.get("content_sha256")
    alias = checkpoint_alias if checkpoint_alias is not None else meta.get("checkpoint_alias")
    repo = checkpoint_repo if checkpoint_repo is not None else meta.get("checkpoint_repo")
    isize = image_size if image_size is not None else meta.get("image_size")

    geometry = polygons_to_geometry(
        items,
        source_kind=source_kind,
        content_sha256=sha,
        checkpoint_alias=alias,
        checkpoint_repo=repo,
        image_size=isize,
        scale_meters_per_unit=scale_meters_per_unit,
        scale_user_confirmed=scale_user_confirmed,
    )
    svg = polygons_to_svg(items)
    extrusion = polygons_to_extrusion(items, wall_height_m=wall_height_m)
    fp = geometry_fingerprint(geometry=geometry, svg=svg, extrusion=extrusion)

    return LayoutBuildResult(
        geometry=geometry,
        svg=svg,
        extrusion=extrusion,
        geometry_fingerprint=fp,
        source_kind=source_kind,
        content_sha256=sha,
        checkpoint_alias=alias,
        checkpoint_repo=repo,
        scale_meters_per_unit=scale_meters_per_unit,
        scale_user_confirmed=scale_user_confirmed,
    )

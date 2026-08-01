"""Assemble Layout JSON (polygons + semantics + scale + metadata)."""

from __future__ import annotations

from typing import Any, Sequence

from services.layout_builder.canonicalize import quantize_points
from services.layout_builder.errors import LayoutBuilderError
from services.raster2seq_adapter.map_output import PolygonItem

SCHEMA_VERSION = "1"


def polygons_to_geometry(
    items: Sequence[PolygonItem],
    *,
    source_kind: str,
    content_sha256: str | None = None,
    checkpoint_alias: str | None = None,
    checkpoint_repo: str | None = "haopt/Raster2Seq",
    image_size: int | None = None,
    scale_meters_per_unit: float | None = None,
    scale_user_confirmed: bool = False,
) -> dict[str, Any]:
    """Build Layout geometry dict for layouts.geometry jsonb."""
    if source_kind not in ("image", "pdf", "text"):
        raise LayoutBuilderError(f"invalid source_kind: {source_kind!r}")

    polygons: list[dict[str, Any]] = []
    for it in items:
        if len(it.points) < 2:
            continue
        polygons.append(
            {
                "id": it.id,
                "label": it.label,
                "kind": it.kind,
                "points": quantize_points(it.points),
            }
        )
    if not polygons:
        raise LayoutBuilderError("no valid polygons (need at least one with ≥2 points)")

    source: dict[str, Any] = {"kind": source_kind}
    if content_sha256 is not None:
        source["content_sha256"] = content_sha256

    checkpoint: dict[str, Any] = {}
    if checkpoint_alias is not None:
        checkpoint["alias"] = checkpoint_alias
    if checkpoint_repo is not None:
        checkpoint["repo"] = checkpoint_repo
    if image_size is not None:
        checkpoint["image_size"] = int(image_size)

    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "checkpoint": checkpoint,
        "scale": {
            "meters_per_unit": scale_meters_per_unit,
            "user_confirmed": bool(scale_user_confirmed),
        },
        "polygons": polygons,
    }

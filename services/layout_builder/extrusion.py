"""3D extrusion: deterministic structure from verified 2D polygons only."""

from __future__ import annotations

from typing import Any, Sequence

from services.layout_builder.canonicalize import quantize_points
from services.raster2seq_adapter.map_output import PolygonItem

DEFAULT_WALL_HEIGHT_M = 2.7
DEFAULT_DOOR_SILL_M = 0.0
DEFAULT_DOOR_HEIGHT_M = 2.1
DEFAULT_WINDOW_SILL_M = 0.9
DEFAULT_WINDOW_HEIGHT_M = 1.2


def _extrude_for_kind(
    kind: str,
    *,
    wall_height_m: float,
    door_sill_m: float,
    door_height_m: float,
    window_sill_m: float,
    window_height_m: float,
) -> dict[str, float]:
    if kind == "door":
        return {"z0": door_sill_m, "z1": door_sill_m + door_height_m}
    if kind == "window":
        return {"z0": window_sill_m, "z1": window_sill_m + window_height_m}
    return {"z0": 0.0, "z1": wall_height_m}


def polygons_to_extrusion(
    items: Sequence[PolygonItem],
    *,
    wall_height_m: float = DEFAULT_WALL_HEIGHT_M,
    door_sill_m: float = DEFAULT_DOOR_SILL_M,
    door_height_m: float = DEFAULT_DOOR_HEIGHT_M,
    window_sill_m: float = DEFAULT_WINDOW_SILL_M,
    window_height_m: float = DEFAULT_WINDOW_HEIGHT_M,
) -> dict[str, Any]:
    """Build extrusion JSON; each node footprint is a copy of 2D points only."""
    nodes: list[dict[str, Any]] = []
    for it in items:
        if len(it.points) < 2:
            continue
        footprint = quantize_points(it.points)
        nodes.append(
            {
                "id": it.id,
                "kind": it.kind,
                "label": it.label,
                "footprint": footprint,
                "extrude": _extrude_for_kind(
                    it.kind,
                    wall_height_m=wall_height_m,
                    door_sill_m=door_sill_m,
                    door_height_m=door_height_m,
                    window_sill_m=window_sill_m,
                    window_height_m=window_height_m,
                ),
            }
        )
    return {
        "wall_height_m": wall_height_m,
        "door": {"sill_m": door_sill_m, "height_m": door_height_m},
        "window": {"sill_m": window_sill_m, "height_m": window_height_m},
        "nodes": nodes,
    }

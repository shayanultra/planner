"""Map Raster2Seq engine.generate output to domain Polygon Sequence items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

# CubiCasa door/window class indices used in predict.py for dataset_name == "cubicasa"
_CUBICASA_DOOR_IDX = 10
_CUBICASA_WINDOW_IDX = 9

# Fallback labels when CC5K_LABEL unavailable (index → name); extended at runtime if possible
_DEFAULT_CC5K: dict[int, str] = {
    0: "background",
    1: "outdoor",
    2: "wall",
    3: "kitchen",
    4: "living_room",
    5: "bedroom",
    6: "bath",
    7: "hallway",
    8: "railing",
    9: "window",
    10: "door",
    11: "other",
}


@dataclass(frozen=True)
class PolygonItem:
    id: str
    label: str
    kind: str  # room | door | window | other
    points: list[list[float]]


def _as_points(poly: Any) -> list[list[float]]:
    arr = np.asarray(poly, dtype=float)
    if arr.ndim != 2 or arr.shape[1] < 2:
        return []
    return [[float(x), float(y)] for x, y in arr[:, :2]]


def _kind_for_class(class_id: int | None) -> str:
    if class_id is None:
        return "room"
    if class_id == _CUBICASA_DOOR_IDX:
        return "door"
    if class_id == _CUBICASA_WINDOW_IDX:
        return "window"
    return "room"


def _label_for_class(class_id: int | None, label_map: dict[int, str]) -> str:
    if class_id is None:
        return "unknown"
    return label_map.get(int(class_id), str(int(class_id)))


def map_generate_output(
    generate_out: dict[str, Any],
    *,
    label_map: dict[int, str] | None = None,
    batch_index: int = 0,
) -> list[PolygonItem]:
    """Convert ``engine.generate`` dict ``{room, labels}`` to PolygonItem list.

    ``room[i]`` is a list of polygons for scene i; ``labels[i]`` parallel class ids.
    """
    rooms = generate_out.get("room") or []
    labels = generate_out.get("labels") or []
    if batch_index >= len(rooms):
        return []

    polys = rooms[batch_index]
    labs = labels[batch_index] if batch_index < len(labels) else []
    lmap = label_map if label_map is not None else _DEFAULT_CC5K

    items: list[PolygonItem] = []
    for i, poly in enumerate(polys):
        points = _as_points(poly)
        if len(points) < 2:
            continue
        class_id: int | None
        if i < len(labs) and labs[i] is not None:
            try:
                class_id = int(labs[i])
            except (TypeError, ValueError):
                class_id = None
        else:
            class_id = None
        items.append(
            PolygonItem(
                id=f"p{i}",
                label=_label_for_class(class_id, lmap),
                kind=_kind_for_class(class_id),
                points=points,
            )
        )
    return items


def apply_polish_to_items(
    items: Sequence[PolygonItem],
    *,
    enabled: bool,
    tolerance: float,
) -> list[PolygonItem]:
    from services.raster2seq_adapter.polish import polish_point_rings

    rings = [it.points for it in items]
    polished = polish_point_rings(rings, enabled=enabled, tolerance=tolerance)
    return [
        PolygonItem(id=it.id, label=it.label, kind=it.kind, points=polished[i])
        for i, it in enumerate(items)
    ]

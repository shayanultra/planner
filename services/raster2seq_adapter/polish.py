"""Optional post-only Douglas-Peucker polish (never primary geometry extraction)."""

from __future__ import annotations

from typing import Sequence

from shapely.geometry import LineString, Polygon
from shapely.validation import make_valid


def polish_point_rings(
    rings: Sequence[Sequence[Sequence[float]]],
    *,
    enabled: bool = False,
    tolerance: float = 1.0,
) -> list[list[list[float]]]:
    """Simplify polygon rings with Douglas-Peucker via shapely.

    When ``enabled`` is False (default), returns a deep copy of input rings unchanged.
    """
    if not enabled:
        return [[list(map(float, pt)) for pt in ring] for ring in rings]

    if tolerance < 0:
        raise ValueError(f"polish tolerance must be >= 0, got {tolerance}")

    out: list[list[list[float]]] = []
    for ring in rings:
        pts = [tuple(map(float, p)) for p in ring]
        if len(pts) < 2:
            out.append([list(p) for p in pts])
            continue
        # Closed ring → Polygon; open → LineString
        closed = len(pts) >= 3 and pts[0] == pts[-1]
        if closed:
            geom = Polygon(pts)
            if not geom.is_valid:
                geom = make_valid(geom)
            if geom.is_empty:
                out.append([list(p) for p in pts])
                continue
            # make_valid may return MultiPolygon; take exterior of largest poly
            if geom.geom_type == "Polygon":
                simplified = geom.simplify(tolerance, preserve_topology=True)
            else:
                polys = [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
                if not polys:
                    out.append([list(p) for p in pts])
                    continue
                simplified = max(polys, key=lambda g: g.area).simplify(
                    tolerance, preserve_topology=True
                )
            if simplified.is_empty or simplified.geom_type != "Polygon":
                out.append([list(p) for p in pts])
                continue
            coords = list(simplified.exterior.coords)
            out.append([[float(x), float(y)] for x, y in coords])
        else:
            line = LineString(pts)
            simplified = line.simplify(tolerance, preserve_topology=True)
            coords = list(simplified.coords)
            out.append([[float(x), float(y)] for x, y in coords])
    return out

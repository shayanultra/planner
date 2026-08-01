"""2D Representation: SVG generated directly from polygon points."""

from __future__ import annotations

from typing import Sequence

from services.layout_builder.canonicalize import quantize_coord
from services.raster2seq_adapter.map_output import PolygonItem

# Fixed decimal places for deterministic SVG path data
_SVG_DECIMALS = 3
_PADDING = 1.0


def _fmt(v: float) -> str:
    return f"{quantize_coord(v, _SVG_DECIMALS):.{_SVG_DECIMALS}f}"


def _points_attr(points: list[list[float]]) -> str:
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points)


def _bbox(items: Sequence[PolygonItem]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for it in items:
        for x, y in it.points:
            xs.append(float(x))
            ys.append(float(y))
    if not xs:
        return 0.0, 0.0, 1.0, 1.0
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_x <= min_x:
        max_x = min_x + 1.0
    if max_y <= min_y:
        max_y = min_y + 1.0
    return min_x, min_y, max_x, max_y


def _style_for_kind(kind: str) -> str:
    if kind == "door":
        return 'fill="none" stroke="#c45c26" stroke-width="0.5"'
    if kind == "window":
        return 'fill="none" stroke="#2a6fdb" stroke-width="0.5"'
    return 'fill="#e8eef5" stroke="#334155" stroke-width="0.35"'


def polygons_to_svg(items: Sequence[PolygonItem]) -> str:
    """Emit deterministic SVG from polygon sequence (input order preserved)."""
    min_x, min_y, max_x, max_y = _bbox(items)
    pad = _PADDING
    vb_x = min_x - pad
    vb_y = min_y - pad
    vb_w = (max_x - min_x) + 2 * pad
    vb_h = (max_y - min_y) + 2 * pad

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{_fmt(vb_x)} {_fmt(vb_y)} {_fmt(vb_w)} {_fmt(vb_h)}" '
        f'data-schema="layout-2d-v1">'
    ]
    for it in items:
        if len(it.points) < 2:
            continue
        pts = _points_attr(it.points)
        style = _style_for_kind(it.kind)
        # Escape attribute values minimally (labels are domain tokens)
        label = it.label.replace('"', "")
        pid = it.id.replace('"', "")
        kind = it.kind.replace('"', "")
        if len(it.points) >= 3:
            tag = (
                f'<polygon points="{pts}" data-id="{pid}" data-kind="{kind}" '
                f'data-label="{label}" {style}/>'
            )
        else:
            tag = (
                f'<polyline points="{pts}" data-id="{pid}" data-kind="{kind}" '
                f'data-label="{label}" {style}/>'
            )
        parts.append(tag)
    parts.append("</svg>")
    return "".join(parts)

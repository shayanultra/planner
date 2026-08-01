"""Canonical JSON dumps and geometry fingerprints for determinism."""

from __future__ import annotations

import hashlib
import json
from typing import Any


COORD_DECIMALS = 6


def quantize_coord(value: float, decimals: int = COORD_DECIMALS) -> float:
    return round(float(value), decimals)


def quantize_points(points: list[list[float]], decimals: int = COORD_DECIMALS) -> list[list[float]]:
    return [[quantize_coord(x, decimals), quantize_coord(y, decimals)] for x, y in points]


def canonical_json(obj: Any) -> str:
    """Stable JSON: sorted keys, no spaces, quantized floats via default."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def geometry_fingerprint(*, geometry: dict[str, Any], svg: str, extrusion: dict[str, Any]) -> str:
    """SHA-256 of canonical geometry + svg + extrusion (identical inputs → identical hash)."""
    payload = canonical_json({"geometry": geometry, "svg": svg, "extrusion": extrusion})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

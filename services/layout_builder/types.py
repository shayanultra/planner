"""Dataclasses for layout build + persist results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class LayoutBuildResult:
    """Pure build output: Layout JSON + 2D SVG + 3D extrusion."""

    geometry: dict[str, Any]
    svg: str
    extrusion: dict[str, Any]
    geometry_fingerprint: str
    source_kind: str
    content_sha256: str | None
    checkpoint_alias: str | None
    checkpoint_repo: str | None
    scale_meters_per_unit: float | None
    scale_user_confirmed: bool


@dataclass(frozen=True)
class LayoutRow:
    """Persisted layouts row + audit metadata."""

    id: UUID
    geometry: dict[str, Any]
    svg: str
    extrusion: dict[str, Any]
    geometry_fingerprint: str
    source_kind: str
    content_sha256: str | None
    scale_meters_per_unit: float | None
    scale_user_confirmed: bool
    audit_id: int | None = None

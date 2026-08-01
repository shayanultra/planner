"""Layout builder: Polygon Sequence → Layout JSON + 2D SVG + 3D extrusion + Postgres (ticket 05)."""

from services.layout_builder.build import build_layout
from services.layout_builder.canonicalize import geometry_fingerprint
from services.layout_builder.errors import LayoutBuilderError, PersistError
from services.layout_builder.extrusion import DEFAULT_WALL_HEIGHT_M, polygons_to_extrusion
from services.layout_builder.geometry import polygons_to_geometry
from services.layout_builder.persist import (
    AUDIT_ACTION,
    build_and_persist_layout,
    connect,
    persist_layout,
    resolve_database_url,
)
from services.layout_builder.svg import polygons_to_svg
from services.layout_builder.types import LayoutBuildResult, LayoutRow

__all__ = [
    "AUDIT_ACTION",
    "DEFAULT_WALL_HEIGHT_M",
    "LayoutBuildResult",
    "LayoutBuilderError",
    "LayoutRow",
    "PersistError",
    "build_and_persist_layout",
    "build_layout",
    "connect",
    "geometry_fingerprint",
    "persist_layout",
    "polygons_to_extrusion",
    "polygons_to_geometry",
    "polygons_to_svg",
    "resolve_database_url",
]

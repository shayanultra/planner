"""Errors for layout builder (ticket 05)."""


class LayoutBuilderError(Exception):
    """Invalid polygons or layout construction failure."""


class PersistError(Exception):
    """Postgres write failure for layouts / audit_log."""

"""Raster2Seq inference adapter (Slice A ticket 04)."""

from services.raster2seq_adapter.checkpoint import (
    CUBICASA5K_ALIAS,
    CUBICASA5K_EXPECTED_BYTES,
    resolve_local_checkpoint,
)
from services.raster2seq_adapter.errors import (
    CheckpointNotFoundError,
    Raster2SeqRuntimeError,
)
from services.raster2seq_adapter.infer import PolygonSequenceResult, infer_polygons
from services.raster2seq_adapter.map_output import PolygonItem
from services.raster2seq_adapter.polish import polish_point_rings

__all__ = [
    "CUBICASA5K_ALIAS",
    "CUBICASA5K_EXPECTED_BYTES",
    "CheckpointNotFoundError",
    "PolygonItem",
    "PolygonSequenceResult",
    "Raster2SeqRuntimeError",
    "infer_polygons",
    "polish_point_rings",
    "resolve_local_checkpoint",
]

"""Errors for Raster2Seq inference adapter."""


class Raster2SeqAdapterError(Exception):
    """Base error for the Raster2Seq adapter."""


class CheckpointNotFoundError(Raster2SeqAdapterError):
    """Raised when the cubicasa5k (or other) checkpoint is missing or wrong size."""


class Raster2SeqRuntimeError(Raster2SeqAdapterError):
    """Raised when vendored Raster2Seq cannot import, build, or run inference."""

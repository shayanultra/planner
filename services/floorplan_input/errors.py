"""Errors for floorplan input normalization."""


class FloorplanInputError(Exception):
    """Base error for input normalization failures."""


class InputNotFoundError(FloorplanInputError):
    """Raised when the input path does not exist."""


class InputConvertError(FloorplanInputError):
    """Raised when PDF→raster conversion or image decode fails."""


class UnsupportedInputError(FloorplanInputError):
    """Raised when the file type is not a supported image or PDF."""

"""Normalize floorplan image/PDF inputs to RGB rasters for Raster2Seq."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image

from services.floorplan_input.errors import (
    InputConvertError,
    InputNotFoundError,
    UnsupportedInputError,
)

SourceKind = Literal["image", "pdf"]

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
_PDF_SUFFIXES = {".pdf"}


@dataclass(frozen=True)
class NormalizedRaster:
    """RGB raster plus source metadata for audit and identical-input detection."""

    rgb: np.ndarray
    source_kind: SourceKind
    content_sha256: str
    page: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.rgb.ndim != 3 or self.rgb.shape[2] != 3:
            raise ValueError("rgb must be HxWx3")
        if self.rgb.dtype != np.uint8:
            raise ValueError("rgb must be uint8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _detect_kind(path: Path) -> SourceKind:
    suffix = path.suffix.lower()
    if suffix in _PDF_SUFFIXES:
        return "pdf"
    if suffix in _IMAGE_SUFFIXES:
        return "image"
    # Magic-byte fallback for extension-less or misnamed files
    try:
        head = path.read_bytes()[:8]
    except OSError as exc:
        raise InputNotFoundError(f"Cannot read input path: {path}") from exc
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n") or head[:2] == b"\xff\xd8":
        return "image"
    raise UnsupportedInputError(
        f"Unsupported floorplan input type for '{path.name}'. "
        f"Expected image ({', '.join(sorted(_IMAGE_SUFFIXES))}) or PDF."
    )


def _load_image_rgb(path: Path) -> np.ndarray:
    try:
        with Image.open(path) as img:
            rgb = np.asarray(img.convert("RGB"), dtype=np.uint8)
    except FileNotFoundError as exc:
        raise InputNotFoundError(f"Input file not found: {path}") from exc
    except OSError as exc:
        raise InputConvertError(f"Failed to decode image '{path}': {exc}") from exc
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise InputConvertError(f"Image did not convert to RGB: shape={rgb.shape}")
    return rgb


def _pdf_to_rgb(
    path: Path,
    *,
    page: int,
    dpi: int,
    pdftoppm_bin: str,
) -> np.ndarray:
    if page < 1:
        raise InputConvertError(f"PDF page must be >= 1, got {page}")
    if dpi < 1:
        raise InputConvertError(f"DPI must be >= 1, got {dpi}")

    with tempfile.TemporaryDirectory(prefix="floorplan_pdf_") as tmp:
        out_prefix = Path(tmp) / "page"
        cmd = [
            pdftoppm_bin,
            "-f",
            str(page),
            "-l",
            str(page),
            "-r",
            str(dpi),
            "-png",
            "-singlefile",
            str(path),
            str(out_prefix),
        ]
        try:
            proc = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise InputConvertError(
                f"pdftoppm not found at '{pdftoppm_bin}'. Install Poppler (e.g. brew install poppler)."
            ) from exc

        if proc.returncode != 0:
            stderr = (proc.stderr or proc.stdout or "").strip()
            raise InputConvertError(
                f"PDF→raster conversion failed for '{path}' (page={page}, dpi={dpi}): {stderr}"
            )

        png_path = Path(f"{out_prefix}.png")
        if not png_path.is_file():
            # Some pdftoppm builds omit -singlefile behavior; try numbered page.
            alt = Path(tmp) / f"page-{page}.png"
            if alt.is_file():
                png_path = alt
            else:
                raise InputConvertError(
                    f"PDF→raster produced no PNG for '{path}' (page={page}). "
                    f"stderr={(proc.stderr or '').strip()}"
                )
        return _load_image_rgb(png_path)


def normalize_floorplan_input(
    path: str | Path,
    *,
    page: int = 1,
    dpi: int = 150,
    pdftoppm_bin: str | None = None,
) -> NormalizedRaster:
    """Load an image or PDF and return an RGB raster suitable for Raster2Seq.

    - Images are converted to RGB (grayscale/RGBA forced to 3 channels).
    - PDFs are rasterized via Poppler ``pdftoppm`` (default page 1, DPI 150).
    - ``content_sha256`` is the SHA-256 of the **source file bytes** (not re-encoded raster).
    """
    input_path = Path(path).expanduser()
    if not input_path.is_file():
        raise InputNotFoundError(f"Input file not found: {input_path}")

    content_sha256 = _sha256_file(input_path)
    kind = _detect_kind(input_path)

    if kind == "image":
        rgb = _load_image_rgb(input_path)
        used_page = 1
    else:
        bin_path = pdftoppm_bin or shutil.which("pdftoppm")
        if not bin_path:
            raise InputConvertError(
                "pdftoppm not found on PATH. Install Poppler (e.g. brew install poppler)."
            )
        rgb = _pdf_to_rgb(
            input_path,
            page=page,
            dpi=dpi,
            pdftoppm_bin=bin_path,
        )
        used_page = page

    height, width = int(rgb.shape[0]), int(rgb.shape[1])
    return NormalizedRaster(
        rgb=rgb,
        source_kind=kind,
        content_sha256=content_sha256,
        page=used_page,
        width=width,
        height=height,
    )

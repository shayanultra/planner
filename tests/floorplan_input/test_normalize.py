"""Behavior tests for normalize_floorplan_input (ticket 03 seam)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from services.floorplan_input import (
    InputConvertError,
    InputNotFoundError,
    UnsupportedInputError,
    normalize_floorplan_input,
)




def _write_png(path: Path, arr: np.ndarray) -> None:
    Image.fromarray(arr, mode="RGB").save(path)


def _minimal_pdf_bytes(text: str = "Floorplan") -> bytes:
    """Tiny valid single-page PDF (no external deps)."""
    # Simple PDF with one page and a text operator omitted for size — blank page is enough.
    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
    )
    stream = f"BT /F1 24 Tf 40 100 Td ({text}) Tj ET".encode("latin-1")
    objects.append(
        b"4 0 obj<< /Length "
        + str(len(stream)).encode()
        + b" >>stream\n"
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
    )

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return bytes(out)


@pytest.fixture
def rgb_png(tmp_path: Path) -> Path:
    path = tmp_path / "sample.png"
    arr = np.zeros((32, 48, 3), dtype=np.uint8)
    arr[:, :] = (10, 20, 30)
    arr[0, 0] = (255, 0, 0)
    _write_png(path, arr)
    return path


@pytest.fixture
def rgba_png(tmp_path: Path) -> Path:
    path = tmp_path / "rgba.png"
    arr = np.zeros((16, 16, 4), dtype=np.uint8)
    arr[:, :] = (1, 2, 3, 128)
    Image.fromarray(arr, mode="RGBA").save(path)
    return path


@pytest.fixture
def gray_png(tmp_path: Path) -> Path:
    path = tmp_path / "gray.png"
    arr = np.full((12, 12), 77, dtype=np.uint8)
    Image.fromarray(arr, mode="L").save(path)
    return path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    path.write_bytes(_minimal_pdf_bytes())
    return path


def test_missing_file_raises_clear_error(tmp_path: Path) -> None:
    missing = tmp_path / "nope.png"
    with pytest.raises(InputNotFoundError, match="not found"):
        normalize_floorplan_input(missing)


def test_image_loads_as_rgb_without_portal(rgb_png: Path) -> None:
    result = normalize_floorplan_input(rgb_png)
    assert result.source_kind == "image"
    assert result.page == 1
    assert result.rgb.shape == (32, 48, 3)
    assert result.rgb.dtype == np.uint8
    assert result.width == 48
    assert result.height == 32
    assert result.rgb[0, 0].tolist() == [255, 0, 0]


def test_rgba_and_grayscale_forced_to_rgb(rgba_png: Path, gray_png: Path) -> None:
    rgba = normalize_floorplan_input(rgba_png)
    assert rgba.rgb.shape == (16, 16, 3)
    assert rgba.rgb[0, 0].tolist() == [1, 2, 3]

    gray = normalize_floorplan_input(gray_png)
    assert gray.rgb.shape == (12, 12, 3)
    assert gray.rgb[0, 0].tolist() == [77, 77, 77]


def test_content_hash_is_sha256_of_source_bytes(rgb_png: Path) -> None:
    expected = hashlib.sha256(rgb_png.read_bytes()).hexdigest()
    result = normalize_floorplan_input(rgb_png)
    assert result.content_sha256 == expected

    again = normalize_floorplan_input(rgb_png)
    assert again.content_sha256 == result.content_sha256


def test_identical_inputs_same_hash(rgb_png: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy.png"
    copy.write_bytes(rgb_png.read_bytes())
    a = normalize_floorplan_input(rgb_png)
    b = normalize_floorplan_input(copy)
    assert a.content_sha256 == b.content_sha256


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("not a floorplan", encoding="utf-8")
    with pytest.raises(UnsupportedInputError, match="Unsupported"):
        normalize_floorplan_input(path)


def test_pdf_converts_via_poppler_default_page_one(sample_pdf: Path) -> None:
    result = normalize_floorplan_input(sample_pdf)
    assert result.source_kind == "pdf"
    assert result.page == 1
    assert result.rgb.ndim == 3
    assert result.rgb.shape[2] == 3
    assert result.rgb.dtype == np.uint8
    assert result.width == result.rgb.shape[1]
    assert result.height == result.rgb.shape[0]
    assert result.height > 0 and result.width > 0
    expected = hashlib.sha256(sample_pdf.read_bytes()).hexdigest()
    assert result.content_sha256 == expected


def test_pdf_convert_failure_clear_error(tmp_path: Path) -> None:
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"%PDF-1.4\nthis is not a valid pdf body")
    with pytest.raises(InputConvertError, match="PDF"):
        normalize_floorplan_input(bad)


def test_pdf_raster_deterministic_for_same_dpi(sample_pdf: Path) -> None:
    a = normalize_floorplan_input(sample_pdf, dpi=72)
    b = normalize_floorplan_input(sample_pdf, dpi=72)
    assert a.content_sha256 == b.content_sha256
    np.testing.assert_array_equal(a.rgb, b.rgb)

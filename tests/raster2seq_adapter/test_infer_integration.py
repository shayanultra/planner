"""Optional real-model integration (skips if Raster2Seq runtime unavailable)."""

from __future__ import annotations

import numpy as np
import pytest

from services.floorplan_input import NormalizedRaster
from services.raster2seq_adapter import Raster2SeqRuntimeError, infer_polygons


def _tiny_rgb() -> NormalizedRaster:
    rgb = np.full((64, 64, 3), 255, dtype=np.uint8)
    # simple dark rectangle
    rgb[16:48, 16:48] = 40
    return NormalizedRaster(
        rgb=rgb,
        source_kind="image",
        content_sha256="b" * 64,
        page=1,
        width=64,
        height=64,
    )


@pytest.mark.integration
def test_real_cubicasa5k_inference_or_skip() -> None:
    try:
        result = infer_polygons(_tiny_rgb(), polish=False)
    except Raster2SeqRuntimeError as exc:
        pytest.skip(f"Raster2Seq runtime unavailable on this host: {exc}")
    assert result.checkpoint_alias == "cubicasa5k"
    assert result.checkpoint_path.endswith("checkpoint.pth")
    assert isinstance(result.polygons, list)
    # polygons may be empty on synthetic noise; metadata is the hard assert
    assert result.image_size >= 64

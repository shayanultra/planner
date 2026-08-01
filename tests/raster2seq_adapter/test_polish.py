"""Douglas-Peucker polish is post-only and toggleable."""

from services.raster2seq_adapter.polish import polish_point_rings


def test_polish_disabled_returns_copy() -> None:
    rings = [[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]]
    out = polish_point_rings(rings, enabled=False)
    assert out == rings
    assert out is not rings


def test_polish_enabled_simplifies_dense_ring() -> None:
    # Square with colinear midpoints — DP should drop midpoints
    rings = [
        [
            [0.0, 0.0],
            [5.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [0.0, 10.0],
            [0.0, 0.0],
        ]
    ]
    out = polish_point_rings(rings, enabled=True, tolerance=1.0)
    assert len(out) == 1
    assert len(out[0]) < len(rings[0])
    assert out[0][0] == out[0][-1]  # closed

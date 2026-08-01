"""Map engine.generate output → PolygonItem."""

import numpy as np

from services.raster2seq_adapter.map_output import (
    apply_polish_to_items,
    map_generate_output,
)


def test_map_generate_output_rooms_and_door() -> None:
    room = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=float)
    door = np.array([[10, 4], [12, 4]], dtype=float)
    gen = {"room": [[room, door]], "labels": [[3, 10]]}
    items = map_generate_output(gen)
    assert len(items) == 2
    assert items[0].kind == "room"
    assert items[0].label == "kitchen"
    assert items[1].kind == "door"
    assert items[1].id == "p1"
    assert items[0].points[0] == [0.0, 0.0]


def test_apply_polish_default_off_preserves() -> None:
    gen = {
        "room": [[np.array([[0, 0], [5, 0], [10, 0], [10, 10], [0, 10], [0, 0]], float)]],
        "labels": [[3]],
    }
    items = map_generate_output(gen)
    same = apply_polish_to_items(items, enabled=False, tolerance=1.0)
    assert same[0].points == items[0].points
    polished = apply_polish_to_items(items, enabled=True, tolerance=1.0)
    assert len(polished[0].points) <= len(items[0].points)

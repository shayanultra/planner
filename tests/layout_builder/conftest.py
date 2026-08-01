"""Shared canned polygons for layout_builder tests (no Raster2Seq)."""

from __future__ import annotations

import pytest

from services.raster2seq_adapter.map_output import PolygonItem


@pytest.fixture
def kitchen_room() -> PolygonItem:
    return PolygonItem(
        id="p0",
        label="kitchen",
        kind="room",
        points=[[0.0, 0.0], [10.0, 0.0], [10.0, 8.0], [0.0, 8.0]],
    )


@pytest.fixture
def door_item() -> PolygonItem:
    return PolygonItem(
        id="p1",
        label="door",
        kind="door",
        points=[[10.0, 3.0], [10.0, 5.0]],
    )


@pytest.fixture
def window_item() -> PolygonItem:
    return PolygonItem(
        id="p2",
        label="window",
        kind="window",
        points=[[2.0, 0.0], [4.0, 0.0]],
    )


@pytest.fixture
def sample_polygons(kitchen_room, door_item, window_item) -> list[PolygonItem]:
    return [kitchen_room, door_item, window_item]

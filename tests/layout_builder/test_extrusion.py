"""3D extrusion derived only from verified 2D footprints."""

from services.layout_builder.canonicalize import quantize_points
from services.layout_builder.extrusion import (
    DEFAULT_DOOR_HEIGHT_M,
    DEFAULT_WALL_HEIGHT_M,
    DEFAULT_WINDOW_SILL_M,
    polygons_to_extrusion,
)
from services.raster2seq_adapter.map_output import PolygonItem


def test_extrusion_footprint_matches_2d(kitchen_room: PolygonItem) -> None:
    ext = polygons_to_extrusion([kitchen_room])
    assert ext["wall_height_m"] == DEFAULT_WALL_HEIGHT_M
    assert len(ext["nodes"]) == 1
    node = ext["nodes"][0]
    assert node["footprint"] == quantize_points(kitchen_room.points)
    assert node["extrude"] == {"z0": 0.0, "z1": DEFAULT_WALL_HEIGHT_M}


def test_door_and_window_use_constants(
    kitchen_room: PolygonItem, door_item: PolygonItem, window_item: PolygonItem
) -> None:
    ext = polygons_to_extrusion([kitchen_room, door_item, window_item])
    by_id = {n["id"]: n for n in ext["nodes"]}
    assert by_id["p1"]["extrude"]["z1"] == DEFAULT_DOOR_HEIGHT_M
    assert by_id["p2"]["extrude"]["z0"] == DEFAULT_WINDOW_SILL_M
    # Footprints are pure copies of 2D — no invented vertices
    assert by_id["p1"]["footprint"] == quantize_points(door_item.points)
    assert by_id["p2"]["footprint"] == quantize_points(window_item.points)


def test_extrusion_deterministic(sample_polygons: list[PolygonItem]) -> None:
    assert polygons_to_extrusion(sample_polygons) == polygons_to_extrusion(sample_polygons)

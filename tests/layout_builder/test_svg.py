"""2D SVG from polygons only."""

from services.layout_builder.svg import polygons_to_svg
from services.raster2seq_adapter.map_output import PolygonItem


def test_svg_contains_polygon_and_points(kitchen_room: PolygonItem) -> None:
    svg = polygons_to_svg([kitchen_room])
    assert svg.startswith("<svg")
    assert "polygon" in svg
    assert 'data-id="p0"' in svg
    assert 'data-kind="room"' in svg
    assert 'data-label="kitchen"' in svg
    assert "0.000,0.000" in svg
    assert "10.000,8.000" in svg


def test_svg_stable_across_calls(sample_polygons: list[PolygonItem]) -> None:
    a = polygons_to_svg(sample_polygons)
    b = polygons_to_svg(sample_polygons)
    assert a == b


def test_svg_door_and_window_as_polyline(door_item: PolygonItem, window_item: PolygonItem) -> None:
    svg = polygons_to_svg([door_item, window_item])
    assert "polyline" in svg
    assert 'data-kind="door"' in svg
    assert 'data-kind="window"' in svg

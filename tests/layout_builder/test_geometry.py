"""Layout JSON assembly."""

import pytest

from services.layout_builder.errors import LayoutBuilderError
from services.layout_builder.geometry import polygons_to_geometry
from services.raster2seq_adapter.map_output import PolygonItem


def test_geometry_has_schema_polygons_scale(sample_polygons: list[PolygonItem]) -> None:
    g = polygons_to_geometry(
        sample_polygons,
        source_kind="image",
        content_sha256="abc123",
        checkpoint_alias="cubicasa5k",
        image_size=256,
        scale_meters_per_unit=0.01,
        scale_user_confirmed=False,
    )
    assert g["schema_version"] == "1"
    assert g["source"]["kind"] == "image"
    assert g["source"]["content_sha256"] == "abc123"
    assert g["checkpoint"]["alias"] == "cubicasa5k"
    assert g["checkpoint"]["image_size"] == 256
    assert g["scale"] == {"meters_per_unit": 0.01, "user_confirmed": False}
    assert len(g["polygons"]) == 3
    assert g["polygons"][0]["label"] == "kitchen"
    assert g["polygons"][0]["kind"] == "room"


def test_empty_polygons_raise() -> None:
    with pytest.raises(LayoutBuilderError):
        polygons_to_geometry([], source_kind="image")


def test_invalid_source_kind(kitchen_room: PolygonItem) -> None:
    with pytest.raises(LayoutBuilderError):
        polygons_to_geometry([kitchen_room], source_kind="dxf")

"""Identical polygon inputs → identical geometry (fingerprint)."""

from services.layout_builder.build import build_layout
from services.layout_builder.canonicalize import geometry_fingerprint
from services.raster2seq_adapter.map_output import PolygonItem


def test_build_layout_identical_inputs_same_fingerprint(
    sample_polygons: list[PolygonItem],
) -> None:
    a = build_layout(
        sample_polygons,
        source_kind="image",
        content_sha256="deadbeef",
        checkpoint_alias="cubicasa5k",
        image_size=256,
    )
    b = build_layout(
        sample_polygons,
        source_kind="image",
        content_sha256="deadbeef",
        checkpoint_alias="cubicasa5k",
        image_size=256,
    )
    assert a.geometry_fingerprint == b.geometry_fingerprint
    assert a.svg == b.svg
    assert a.extrusion == b.extrusion
    assert a.geometry == b.geometry
    # Fingerprint recomputed from parts matches
    assert (
        geometry_fingerprint(geometry=a.geometry, svg=a.svg, extrusion=a.extrusion)
        == a.geometry_fingerprint
    )


def test_perturbed_point_changes_fingerprint(kitchen_room: PolygonItem) -> None:
    a = build_layout([kitchen_room], source_kind="image")
    other = PolygonItem(
        id=kitchen_room.id,
        label=kitchen_room.label,
        kind=kitchen_room.kind,
        points=[[0.0, 0.0], [10.0, 0.0], [10.0, 8.1], [0.0, 8.0]],
    )
    b = build_layout([other], source_kind="image")
    assert a.geometry_fingerprint != b.geometry_fingerprint


def test_extrusion_nodes_only_from_2d_polygons(sample_polygons: list[PolygonItem]) -> None:
    result = build_layout(sample_polygons, source_kind="pdf")
    assert result.source_kind == "pdf"
    for node, poly in zip(result.extrusion["nodes"], sample_polygons, strict=True):
        # quantized equality
        assert len(node["footprint"]) == len(poly.points)
        assert node["id"] == poly.id

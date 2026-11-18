import copy
import xml.etree.ElementTree as ET
from types import SimpleNamespace
import pytest
from fontTools.ufoLib.glifLib import readGlyphFromString
from fontTools.pens.recordingPen import RecordingPointPen
from fontlab8_mcp.glif_exchange import xml_from_source, source_from_xml


def source(types, closed):
    return dict(
        version=1,
        glyph_name="A",
        layer_name="Regular",
        advance_width=600,
        anchors=[
            dict(
                name="top",
                x=100,
                y=700,
                expression_x="",
                expression_y="",
                cloud_enabled=False,
            )
        ],
        shapes=[
            dict(
                shape_index=0,
                shape_transform=[1, 0, 0, 1, 0, 0],
                unsupported=False,
                contours=[
                    dict(
                        contour_index=0,
                        closed=closed,
                        nodes=[
                            dict(
                                node_index=i,
                                x=i * 100,
                                y=(i % 2) * 100,
                                type=t,
                                smooth=False,
                            )
                            for i, t in enumerate(types)
                        ],
                    )
                ],
            )
        ],
    )


@pytest.mark.parametrize(
    "types,closed",
    [
        (["on", "curve", "curve", "on"], True),
        (["on", "curve", "curve", "on"], False),
        (["on", "off", "on"], True),
        (["off", "off"], True),
    ],
)
def test_cubic_quadratic_and_open_glif_roundtrip(types, closed):
    original = source(types, closed)
    text = xml_from_source(original)
    pen = RecordingPointPen()
    readGlyphFromString(text, SimpleNamespace(), pen)
    assert len([v for v in pen.value if v[0] == "addPoint"]) == len(types)
    assert source_from_xml(text, original) == original
    root = ET.fromstring(text)
    root.find("./outline/contour/point").set("x", "42")
    changed = source_from_xml(ET.tostring(root, encoding="unicode"), original)
    assert changed["shapes"][0]["contours"][0]["nodes"][0]["x"] == 42
    assert original["shapes"][0]["contours"][0]["nodes"][0]["x"] == 0


def test_glif_rejects_topology_components_entities_and_transforms():
    original = source(["on", "on", "on"], True)
    text = xml_from_source(original)
    root = ET.fromstring(text)
    root.find("./outline/contour").remove(root.find("./outline/contour/point"))
    with pytest.raises(ValueError):
        source_from_xml(ET.tostring(root, encoding="unicode"), original)
    with pytest.raises(ValueError):
        source_from_xml("<!DOCTYPE glyph>" + text, original)
    root = ET.fromstring(text)
    ET.SubElement(root.find("outline"), "component", base="V")
    with pytest.raises(ValueError):
        source_from_xml(ET.tostring(root, encoding="unicode"), original)
    transformed = copy.deepcopy(original)
    transformed["shapes"][0]["shape_transform"][-2] = 20
    with pytest.raises(ValueError):
        xml_from_source(transformed)

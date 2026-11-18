"""Host-side standard GLIF exchange for existing native contour topology."""

import copy
import xml.etree.ElementTree as ET


def xml_from_source(source):
    root = ET.Element("glyph", name=source["glyph_name"], format="2")
    ET.SubElement(root, "advance", width=str(source["advance_width"]))
    for a in source["anchors"]:
        ET.SubElement(root, "anchor", name=a["name"], x=str(a["x"]), y=str(a["y"]))
    outline = ET.SubElement(root, "outline")
    for shape in source["shapes"]:
        if shape["unsupported"] or shape["shape_transform"] != [1, 0, 0, 1, 0, 0]:
            raise ValueError(
                "GLIF exchange currently requires non-component identity-transform shapes; use native JSON for local transforms"
            )
        for contour in shape["contours"]:
            ci = f"s{shape['shape_index']}c{contour['contour_index']}"
            element = ET.SubElement(outline, "contour", identifier=ci)
            ns = contour["nodes"]
            for i, n in enumerate(ns):
                attr = dict(x=str(n["x"]), y=str(n["y"]), identifier=ci + "n" + str(i))
                if n["type"] == "on":
                    prev = ns[i - 1]["type"] if i or contour["closed"] else None
                    attr["type"] = (
                        "move"
                        if not contour["closed"] and i == 0
                        else (
                            "curve"
                            if prev == "curve"
                            else "qcurve" if prev == "off" else "line"
                        )
                    )
                    if n["smooth"]:
                        attr["smooth"] = "yes"
                ET.SubElement(element, "point", attr)
    ET.indent(root)
    return ET.tostring(root, encoding="unicode")


def source_from_xml(text, original):
    if (
        len(text.encode()) > 1024 * 1024
        or "<!DOCTYPE" in text.upper()
        or "<!ENTITY" in text.upper()
    ):
        raise ValueError("GLIF must be <=1 MiB without entities/DOCTYPE")
    root = ET.fromstring(text)
    if (
        root.tag != "glyph"
        or root.get("name") != original["glyph_name"]
        or root.get("format") != "2"
    ):
        raise ValueError("Expected same glyph name and GLIF format 2")
    if (
        set(root.attrib) != {"name", "format"}
        or len(root.findall("outline")) != 1
        or any(e.tag != "contour" for e in root.find("outline"))
    ):
        raise ValueError("GLIF identity and one contour-only outline required")
    # Original identifiers and type attributes make reordering or topology edits explicit.
    expected = ET.fromstring(xml_from_source(original))
    new = copy.deepcopy(original)
    expected_contours = expected.findall("./outline/contour")
    incoming = root.findall("./outline/contour")
    if any(e.tag not in ("advance", "outline", "anchor") for e in root):
        raise ValueError(
            "Only advance, outline and anchors are writable in this GLIF exchange"
        )
    if root.findall("./outline/component") or len(incoming) != len(expected_contours):
        raise ValueError("Contour topology/component changes are not supported")
    cursor = 0
    for shape in new["shapes"]:
        for contour in shape["contours"]:
            actual, baseline = incoming[cursor], expected_contours[cursor]
            cursor += 1
            if actual.attrib != baseline.attrib or len(actual) != len(baseline):
                raise ValueError("Contour identity/node count changed")
            for node, element, prior in zip(contour["nodes"], actual, baseline):
                if element.tag != "point" or {
                    k: v for k, v in element.attrib.items() if k not in ("x", "y")
                } != {k: v for k, v in prior.attrib.items() if k not in ("x", "y")}:
                    raise ValueError("GLIF node identity/type/smooth changed")
                node["x"] = float(element.attrib["x"])
                node["y"] = float(element.attrib["y"])
    advances = root.findall("advance")
    if len(advances) != 1 or set(advances[0].attrib) != {"width"}:
        raise ValueError("Exactly one advance width required")
    new["advance_width"] = float(advances[0].get("width"))
    before = {a["name"]: a for a in original["anchors"]}
    result = []
    for a in root.findall("anchor"):
        if set(a.attrib) != {"name", "x", "y"}:
            raise ValueError("Anchor must have name/x/y")
        name = a.get("name")
        x, y = float(a.get("x")), float(a.get("y"))
        record = copy.deepcopy(
            before.get(
                name,
                dict(name=name, expression_x="", expression_y="", cloud_enabled=True),
            )
        )
        if (
            name in before
            and (x != before[name]["x"] or y != before[name]["y"])
            and (record["expression_x"] or record["expression_y"])
        ):
            raise ValueError("Use JSON to edit anchors with expressions")
        record.update(x=x, y=y)
        result.append(record)
    new["anchors"] = result
    return new

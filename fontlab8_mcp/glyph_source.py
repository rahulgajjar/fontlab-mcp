"""Revision-guarded whole-layer coordinate exchange, preserving native topology."""

import hashlib
import json
import fontlab
from PythonQt.QtCore import QPointF
from .glyph_access import resolve, nodes, anchors, finite


def read(p, args):
    g, l = resolve(p, args)
    source = dict(
        version=1,
        glyph_name=g.name,
        layer_name=l.name,
        advance_width=l.advanceWidth,
        shapes=nodes(l, {})["shapes"],
        anchors=anchors(l),
    )
    for si, s in enumerate(l.shapes):
        if not s.isComponent:
            for ci, c in enumerate(s.contours):
                source["shapes"][si]["contours"][ci]["closed"] = c.closed
    revision = hashlib.sha256(
        json.dumps(source, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    return dict(
        revision=revision,
        source=source,
        layers=[
            dict(
                name=v.name,
                is_master=v.isMasterLayer,
                is_background=v.isMaskLayer,
                is_service=v.isService,
                is_auto=v.autoLayer,
            )
            for v in g.layers
        ],
    )


def write(p, args, notify):
    current = read(p, args)
    old = current["source"]
    new = args["source"]
    if args["revision"] != current["revision"]:
        raise ValueError("Stale glyph revision; read source again")
    if not isinstance(new, dict) or set(new) != set(old):
        raise ValueError("Source structure must match get_glyph_source")
    for key in ("version", "glyph_name", "layer_name"):
        if new[key] != old[key]:
            raise ValueError("Source identity changed; use scoped metadata tools")
    g, l = resolve(p, args)
    if l.autoLayer or any((l.metricsLeft, l.metricsRight, l.metricsWidth)):
        raise ValueError("Auto/bound metric layers cannot be replaced")
    if len(new["shapes"]) != len(old["shapes"]):
        raise ValueError("Shape topology changes are not supported")
    plans = []
    for si, (target, prior) in enumerate(zip(new["shapes"], old["shapes"])):
        if prior["unsupported"]:
            raise ValueError("Component source editing not qualified")
        if set(target) != set(prior) or any(
            target[k] != prior[k] for k in prior if k != "contours"
        ):
            raise ValueError("Shape transform/identity changed")
        if len(target["contours"]) != len(prior["contours"]):
            raise ValueError("Contour count changed")
        for ci, (contour, before) in enumerate(
            zip(target["contours"], prior["contours"])
        ):
            if set(contour) != set(before) or any(
                contour[k] != before[k] for k in before if k != "nodes"
            ):
                raise ValueError("Contour identity/closure changed")
            if len(contour["nodes"]) != len(before["nodes"]):
                raise ValueError(
                    "Node count changed; coordinate exchange preserves topology"
                )
            for ni, (node, prev) in enumerate(zip(contour["nodes"], before["nodes"])):
                if set(node) != set(prev) or any(
                    node[k] != prev[k] for k in prev if k not in ("x", "y")
                ):
                    raise ValueError("Node type/smooth/identity changed")
                plans.append(
                    (
                        l.shapes[si].contours[ci].nodes()[ni],
                        finite(node["x"]),
                        finite(node["y"]),
                        prev["x"],
                        prev["y"],
                    )
                )
    finite(new["advance_width"])
    if not isinstance(new["anchors"], list) or len(new["anchors"]) > 64:
        raise ValueError("At most 64 anchors")
    seen = set()
    for a in new["anchors"]:
        if set(a) != {
            "name",
            "x",
            "y",
            "expression_x",
            "expression_y",
            "cloud_enabled",
        }:
            raise ValueError("Invalid anchor fields")
        if (
            not isinstance(a["name"], str)
            or not a["name"]
            or len(a["name"]) > 128
            or a["name"] in seen
        ):
            raise ValueError("Invalid/duplicate anchor name")
        seen.add(a["name"])
        finite(a["x"])
        finite(a["y"])
        if not isinstance(a["cloud_enabled"], bool):
            raise ValueError("cloud_enabled must be boolean")
        for k in ("expression_x", "expression_y"):
            if not isinstance(a[k], str) or len(a[k]) > 256:
                raise ValueError("Invalid anchor expression")
    if args.get("dry_run"):
        return dict(
            dry_run=True,
            revision=current["revision"],
            node_count=len(plans),
            anchor_count=len(seen),
        )
    previous_objects = {a.name: a for a in l.anchors}

    def apply_anchors(records):
        wanted = {v["name"] for v in records}
        for a in list(l.anchors):
            if a.name not in wanted:
                l.removeAnchor(a)
        for v in records:
            a = next((x for x in l.anchors if x.name == v["name"]), None)
            if a is None:
                a = previous_objects.get(v["name"]) or fontlab.flPinPoint(
                    QPointF(v["x"], v["y"])
                )
                a.name = v["name"]
                a.anchor = True
                l.addAnchor(a)
            a.point = QPointF(v["x"], v["y"])
            a.expressionX = v["expression_x"]
            a.expressionY = v["expression_y"]
            a.cloudEnabled = v["cloud_enabled"]

    try:
        for node, x, y, _, _ in plans:
            node.x = x
            node.y = y
        l.advanceWidth = new["advance_width"]
        apply_anchors(new["anchors"])
        g.update()
        notify(p, "MCP glyph source coordinates")
    except Exception:
        for node, _, _, x, y in plans:
            node.x = x
            node.y = y
        l.advanceWidth = old["advance_width"]
        apply_anchors(old["anchors"])
        g.update()
        raise
    result = read(p, args)
    result["undo_supported"] = False
    return result

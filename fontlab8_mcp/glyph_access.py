"""Native layer, node and anchor access; deliberately scoped partial contracts."""

import math
import fontlab
from PythonQt.QtCore import QPointF

NAMES = {"get_glyph", "get_glyph_nodes", "edit_glyph_nodes", "set_glyph_anchors"}


def resolve(p, args):
    candidates = [v for v in p.fgPackage.glyphs if v.name == args["glyph_name"]]
    if len(candidates) != 1:
        raise ValueError("Exact existing glyph required")
    g = fontlab.flGlyph(candidates[0])
    layers = (
        [v for v in g.layers if v.name == args["layer_name"]]
        if "layer_name" in args
        else [g.activeLayer]
    )
    if len(layers) != 1 or layers[0] is None:
        raise ValueError("Exact existing layer required")
    return g, layers[0]


def finite(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError("Finite coordinate required")
    return value


def anchors(l):
    return [
        dict(
            name=a.name,
            x=a.point.x(),
            y=a.point.y(),
            expression_x=a.expressionX,
            expression_y=a.expressionY,
            cloud_enabled=a.cloudEnabled,
        )
        for a in l.anchors
    ]


def nodes(l, args):
    if "contour_index" in args and "shape_index" not in args:
        raise ValueError("contour_index requires shape_index")
    rows = []
    for si, s in enumerate(l.shapes):
        if "shape_index" in args and args["shape_index"] != si:
            continue
        tr = s.transform
        row = dict(
            shape_index=si,
            shape_transform=[tr.m11(), tr.m12(), tr.m21(), tr.m22(), tr.dx(), tr.dy()],
            unsupported=bool(s.isComponent),
            contours=[],
        )
        if not s.isComponent:
            for ci, c in enumerate(s.contours):
                if "contour_index" in args and args["contour_index"] != ci:
                    continue
                row["contours"].append(
                    dict(
                        contour_index=ci,
                        nodes=[
                            dict(
                                node_index=i, x=n.x, y=n.y, type=n.type, smooth=n.smooth
                            )
                            for i, n in enumerate(c.nodes())
                        ],
                    )
                )
        rows.append(row)
    return dict(layer_name=l.name, shapes=rows, extrema_analysis_supported=False)


def dispatch(name, args, p, notify):
    g, l = resolve(p, args)
    if name == "get_glyph":
        if args.get("detail") != "construction":
            raise ValueError(
                "Only detail=construction is ported; full writable VFJ glyph not returned"
            )
        if "mark_glyph" in args or "component_index" in args:
            raise ValueError("Attachment candidate analysis not ported")
        return dict(
            glyph_name=g.name,
            layer_name=l.name,
            advance_width=l.advanceWidth,
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
            anchors=anchors(l),
            component_detail_supported=False,
            shape_count=len(l.shapes),
        )
    if name == "get_glyph_nodes":
        return nodes(l, args)
    if l.autoLayer:
        raise ValueError("Auto layers cannot be edited by this tool")
    if name == "edit_glyph_nodes":
        staged = {}
        original = {}
        objects = {}
        for op in args["operations"]:
            allowed = {"op", "shape_index", "contour_index", "node_index"} | (
                {"x", "y"} if op["op"] == "set" else {"dx", "dy", "move_handles"}
            )
            if set(op) - allowed:
                raise ValueError("Unsupported fields for coordinate operation")
            if op["op"] not in ("set", "move") or any(
                k in op for k in ("type", "smooth")
            ):
                raise ValueError("Only coordinate set/move operations qualified")
            si, ci, ni = op["shape_index"], op["contour_index"], op.get("node_index")
            if any(
                not isinstance(v, int) or isinstance(v, bool) or v < 0
                for v in (si, ci, ni)
            ):
                raise ValueError("Nonnegative node/contour/shape indices required")
            if si >= len(l.shapes):
                raise ValueError("Shape index out of range")
            s = l.shapes[si]
            if s.isComponent:
                raise ValueError("Edit component source instead")
            if ci >= len(s.contours):
                raise ValueError("Contour index out of range")
            ns = s.contours[ci].nodes()
            if ni >= len(ns):
                raise ValueError("Node index out of range")

            def remember(i):
                key = (si, ci, i)
                objects[key] = ns[i]
                if key not in staged:
                    original[key] = (ns[i].x, ns[i].y)
                    staged[key] = original[key]
                return key

            key = remember(ni)
            x, y = staged[key]
            if op["op"] == "set":
                if "x" not in op and "y" not in op:
                    raise ValueError("set requires x or y")
                staged[key] = (finite(op.get("x", x)), finite(op.get("y", y)))
            else:
                dx, dy = finite(op.get("dx")), finite(op.get("dy"))
                staged[key] = (finite(x + dx), finite(y + dy))
                if op.get("move_handles", True) and ns[ni].type == "on":
                    for direction in (-1, 1):
                        for step in range(1, len(ns)):
                            raw_index = ni + direction * step
                            if not s.contours[ci].closed and not 0 <= raw_index < len(
                                ns
                            ):
                                break
                            index = raw_index % len(ns)
                            if ns[index].type == "on":
                                break
                            hk = remember(index)
                            hx, hy = staged[hk]
                            staged[hk] = (finite(hx + dx), finite(hy + dy))
        if not args.get("dry_run"):
            try:
                for key, (x, y) in staged.items():
                    objects[key].x = x
                    objects[key].y = y
                g.update()
                notify(p, "MCP node edit")
            except Exception:
                for key, (x, y) in original.items():
                    objects[key].x = x
                    objects[key].y = y
                g.update()
                raise
        return dict(
            dry_run=args.get("dry_run", False),
            undo_supported=False,
            changed_nodes=[
                dict(
                    shape_index=k[0],
                    contour_index=k[1],
                    node_index=k[2],
                    x=v[0],
                    y=v[1],
                )
                for k, v in staged.items()
            ],
        )
    if name == "set_glyph_anchors":
        plans = []
        seen = set()
        for patch in args["anchors"]:
            if patch["name"] in seen:
                raise ValueError("Duplicate anchor name")
            seen.add(patch["name"])
            if "mark_enabled" in patch:
                raise ValueError("mark_enabled not qualified on FontLab 8")
            existing = next((a for a in l.anchors if a.name == patch["name"]), None)
            if patch.get("remove"):
                if set(patch) - {"name", "remove"}:
                    raise ValueError("Remove accepts only name/remove")
                plans.append((patch, existing))
                continue
            if existing is None and not {"x", "y"} <= set(patch):
                raise ValueError("New anchor requires x/y")
            for axis in ("x", "y"):
                if axis in patch:
                    finite(patch[axis])
            plans.append((patch, existing))
        # Full batch preflight precedes mutation. Native setters are qualified below,
        # but expression evaluation and native undo are explicitly not guaranteed.
        for patch, a in plans:
            if patch.get("remove"):
                if a is not None:
                    l.removeAnchor(a)
                continue
            if a is None:
                a = fontlab.flPinPoint(QPointF(patch["x"], patch["y"]))
                a.name = patch["name"]
                a.anchor = True
                l.addAnchor(a)
            a.point = QPointF(patch.get("x", a.point.x()), patch.get("y", a.point.y()))
            for axis in ("x", "y"):
                key = "expression_" + axis
                if key in patch or axis in patch:
                    setattr(a, "expression" + axis.upper(), patch.get(key, ""))
            if "cloud_enabled" in patch:
                a.cloudEnabled = patch["cloud_enabled"]
        g.update()
        notify(p, "MCP anchor edit")
        return dict(
            glyph_name=g.name,
            layer_name=l.name,
            anchors=anchors(l),
            undo_supported=False,
        )

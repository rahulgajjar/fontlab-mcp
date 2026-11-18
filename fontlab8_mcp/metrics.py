"""Manual native spacing; no autospacing or automatic kerning."""

import math
import fontlab
from PythonQt.QtGui import QTransform


def finite(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError("Finite metric value required")
    return v


def read(g):
    l = g.activeLayer
    b = l.boundingBox
    empty = not l.hasShapeData
    return dict(
        advance_width=l.advanceWidth,
        lsb=None if empty else b.left(),
        rsb=None if empty else l.advanceWidth - b.right(),
        layer_name=l.name,
        metrics_left=l.metricsLeft,
        metrics_right=l.metricsRight,
        metrics_width=l.metricsWidth,
    )


def edit(g, args):
    allowed = {"font_id", "font_name", "glyph_name", "advance_width", "lsb", "rsb"}
    if set(args) - allowed:
        raise ValueError("Metric expressions are not qualified; numeric spacing only")
    l = g.activeLayer
    if l.autoLayer:
        raise ValueError("Auto layer numeric spacing not qualified")
    before = read(g)
    if any((l.metricsLeft, l.metricsRight, l.metricsWidth)):
        raise ValueError(
            "Bound metric expressions must be reviewed before numeric spacing"
        )
    for key in ("lsb", "rsb", "advance_width"):
        if key in args:
            finite(args[key])
    if any(key in args for key in ("lsb", "rsb")) and before["lsb"] is None:
        raise ValueError("Sidebearings undefined for empty glyph")
    dx = (
        args.get("lsb", before["lsb"]) - before["lsb"]
        if before["lsb"] is not None
        else 0
    )
    width = before["advance_width"] + dx
    if "advance_width" in args:
        width = args["advance_width"]
    if "rsb" in args:
        target = l.boundingBox.right() + dx + args["rsb"]
        if "advance_width" in args and abs(width - target) > 1e-7:
            raise ValueError("advance_width conflicts with requested lsb/rsb")
        width = target
    finite(width)
    try:
        if dx:
            l.applyTransform(QTransform().translate(dx, 0))
        l.advanceWidth = width
        g.update()
    except Exception:
        if dx:
            l.applyTransform(QTransform().translate(-dx, 0))
        l.advanceWidth = before["advance_width"]
        g.update()
        raise
    return read(g)

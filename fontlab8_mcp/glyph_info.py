"""FontLab 8 extensions for scoped bulk glyph metadata edits, not replacement."""

import re
import fontlab


def record(fg):
    g = fontlab.flGlyph(fg)
    from .metrics import read

    return dict(
        **read(g),
        glyph_name=fg.name,
        note=g.note,
        mark=g.mark,
        tags=list(g.tags),
        unicodes=list(fg.unicodes),
    )


def dispatch(name, args, p, notify):
    mapping = {g.name: g for g in p.fgPackage.glyphs}
    if name == "get_glyph_info":
        names = args.get("glyph_names", list(mapping))
        if any(n not in mapping for n in names):
            raise ValueError("Unknown glyph")
        return dict(glyphs=[record(mapping[n]) for n in names])
    plans = []
    target_names = set()
    seen = set()
    for patch in args["edits"]:
        n = patch["glyph_name"]
        if "new_name" in patch:
            new = patch["new_name"]
            if (
                not re.fullmatch(r"[A-Za-z_.][A-Za-z_0-9.]*", new)
                or len(new) > 128
                or new in mapping
                and new != n
            ):
                raise ValueError("Invalid or existing glyph name")
        if n in seen or n not in mapping:
            raise ValueError("Duplicate or unknown glyph: " + n)
        if n == ".notdef" and patch.get("new_name", n) != n:
            raise ValueError(".notdef cannot be renamed")
        target = patch.get("new_name", n)
        if target in target_names:
            raise ValueError("Duplicate target glyph name")
        target_names.add(target)
        seen.add(n)
        for u in patch.get("unicodes", []):
            if (
                not isinstance(u, int)
                or isinstance(u, bool)
                or not 0 <= u <= 0x10FFFF
                or 0xD800 <= u <= 0xDFFF
            ):
                raise ValueError("Invalid Unicode scalar")
        if len(set(patch.get("unicodes", []))) != len(patch.get("unicodes", [])):
            raise ValueError("Duplicate Unicode")
        plans.append((mapping[n], patch, record(mapping[n])))

    def apply(fg, patch):
        g = fontlab.flGlyph(fg)
        for key in ("note", "mark"):
            if key in patch:
                setattr(g, key, patch[key])
        if "tags" in patch:
            for tag in set(g.tags) - set(patch["tags"]):
                g.setTag(tag, False)
            for tag in patch["tags"]:
                g.setTag(tag, True)
        if "unicodes" in patch:
            fg.unicodes = patch["unicodes"]
        if "new_name" in patch:
            g.name = fg.name = patch["new_name"]
        g.update()

    try:
        for fg, patch, _ in plans:
            apply(fg, patch)
        notify(p, "MCP bulk glyph metadata")
    except Exception:
        for fg, _, before in plans:
            apply(fg, dict(before, new_name=before["glyph_name"]))
        raise
    return dict(glyphs=[record(fg) for fg, _, _ in plans], undo_supported=False)

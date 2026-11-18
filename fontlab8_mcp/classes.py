"""Native OpenType class membership. Kerning classes are deliberately read-only."""

import hashlib, json, re
import fontlab, fontgate


def read(p):
    records = []
    panel = p.getAllGroups() or []
    marks = {item[1]: item[3] for item in panel}
    for name, g in sorted(p.fgPackage.groups.asDict().items()):
        records.append(
            dict(
                name=name,
                glyph_names=list(g),
                mode=g.mode,
                mark=marks.get(name),
                editable=g.mode == "FeaClassGroupMode",
            )
        )
    order = [g.name for g in p.fgPackage.glyphs]
    revision = hashlib.sha256(
        json.dumps([records, order], sort_keys=True).encode()
    ).hexdigest()
    return dict(
        revision=revision,
        classes=records,
        native_panel=[
            dict(is_kerning=bool(v[0]), name=v[1], id=v[2], mark=v[3], glyph_names=v[4])
            for v in panel
        ],
    )


def write(p, args, notify):
    old = read(p)
    if args["revision"] != old["revision"]:
        raise ValueError("Stale class revision")
    prior = p.fgPackage.groups.asDict()
    result = dict(prior)
    names = set()
    glyphs = {g.name for g in p.fgPackage.glyphs}
    marks = {item["name"]: item["mark"] for item in old["classes"]}
    for edit in args["edits"]:
        name = edit["name"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9.]*", name) or name in names:
            raise ValueError("Invalid/duplicate class name; omit @")
        names.add(name)
        if name in prior and prior[name].mode != "FeaClassGroupMode":
            raise ValueError(
                "Only OpenType classes editable; kerning groups are not qualified"
            )
        if marks.get(name) not in (None, 0):
            raise ValueError(
                "Class color mark preservation not qualified; nonzero-mark class left unchanged"
            )
        if edit.get("remove"):
            if set(edit) != {"name", "remove"}:
                raise ValueError("Removal accepts only name/remove")
            result.pop(name, None)
            continue
        members = edit.get("glyph_names")
        if (
            not isinstance(members, list)
            or not members
            or len(members) != len(set(members))
            or not set(members) <= glyphs
        ):
            raise ValueError("Nonempty unique existing glyph names required")
        result[name] = fontgate.fgGroup(name, members, "FeaClassGroupMode", members[0])
    if args.get("dry_run"):
        return dict(dry_run=True, revision=old["revision"])
    from .layout_buffer import capture, restore

    previous_tables = capture(p)
    try:
        p.fgPackage.groups.fromDict(result)
        fontlab.flItems.notifyFeaturesChanged(p.fgId, False)
        notify(p, "MCP OpenType class membership")
    except Exception:
        p.fgPackage.groups.fromDict(prior)
        raise
    finally:
        restore(p, previous_tables)
    value = read(p)
    value.update(
        undo_supported=False,
        note="OpenType membership only; class IDs may change. Feature source references are not rewritten; raw stored layout bytes are preserved; visual Lookup behavior is not qualified.",
    )
    return value

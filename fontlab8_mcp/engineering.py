"""Stored table publication and native hinting inspection; no automatic hinting."""

import base64, hashlib, json
from pathlib import Path
import fontlab

MANAGED = ("GDEF", "GPOS", "GSUB")


def table_rows(tables, include=False):
    rows = []
    for tag, data in sorted(tables.items()):
        row = dict(
            tag=tag, byte_count=len(data), sha256=hashlib.sha256(data).hexdigest()
        )
        if include:
            row["data_base64"] = base64.b64encode(data).decode()
        rows.append(row)
    return rows


def stored(p, args):
    from .layout_buffer import hydrate, ARCHIVE

    storage = hydrate(p)
    raw = {tag: bytes(p.fgPackage.tables[tag]) for tag in p.fgPackage.tables.keys()}
    tags = args.get("tags", sorted(raw))
    if any(not isinstance(t, str) or len(t) != 4 for t in tags) or len(tags) != len(
        set(tags)
    ):
        raise ValueError("Unique four-character tags required")
    if set(tags) - set(raw):
        raise ValueError(
            "Requested table is not stored: " + ", ".join(sorted(set(tags) - set(raw)))
        )
    selected = {t: raw[t] for t in tags}
    fmt = args.get("format", "json")
    path = Path(args["output_path"]) if "output_path" in args else None
    if fmt not in ("json", "binary"):
        raise ValueError("format must be json or binary")
    if fmt == "binary" and (path is None or len(tags) != 1):
        raise ValueError("Binary export requires output_path and exactly one tag")
    archive_revision = p.packageLib.get(ARCHIVE, {}).get("compiled_revision")
    from .features import read

    matches_source = (
        (read(p)["revision"] == archive_revision) if archive_revision else None
    )
    include = args.get("include_data", path is not None)
    if path is None and include and sum(len(v) for v in selected.values()) > 512 * 1024:
        raise ValueError("Inline byte limit exceeded; export to output_path")
    if path is not None:
        if not path.is_absolute():
            raise ValueError("Absolute output_path required")
        if path.exists() and not args.get("overwrite"):
            raise ValueError("Output exists")
        payload = (
            next(iter(selected.values()))
            if fmt == "binary"
            else json.dumps(
                dict(tables=table_rows(selected, include)), indent=2
            ).encode()
        )
        with path.open("wb" if args.get("overwrite") else "xb") as stream:
            stream.write(payload)
    return dict(
        storage=storage,
        source_matches_archived_compilation=matches_source,
        archived_compiled_revision=p.packageLib.get(ARCHIVE, {}).get(
            "compiled_revision"
        ),
        font_id=p.fgId,
        tables=table_rows(selected, include and path is None),
        output_path=str(path) if path else None,
        source="native stored table bytes; not a new export or compilation",
    )


def publish(p, args, notify):
    from .features import read

    if read(p)["revision"] != args["revision"]:
        raise ValueError("Stale features/classes/glyph-order revision")
    if "compiled_tables" not in args:
        raise ValueError(
            "compile_features must use the MCP stdio compiler preparation path"
        )
    data = args["compiled_tables"]
    if set(data) - set(MANAGED):
        raise ValueError("Only GSUB/GPOS/GDEF publication is supported")
    decoded = {
        tag: base64.b64decode(value, validate=True) for tag, value in data.items()
    }
    if sum(len(v) for v in decoded.values()) > 1024 * 1024:
        raise ValueError("Compiled publication limit is 1 MiB")
    report = dict(
        revision=args["revision"],
        tables=table_rows(decoded),
        warnings=args.get("compiler_warnings", []),
        compiler="FontTools feaLib",
        dry_run=args.get("dry_run", False),
        undo_supported=False,
    )
    if args.get("dry_run"):
        return report
    from .layout_buffer import hydrate, persist, MAX_BYTES

    hydrate(p)
    before_library = dict(p.packageLib)
    t = p.fgPackage.tables
    if (
        sum(len(t[tag]) for tag in t.keys() if tag not in MANAGED)
        + sum(map(len, decoded.values()))
        > MAX_BYTES
    ):
        raise ValueError("Stored-table archive would exceed 8 MiB")
    old = {tag: bytes(t[tag]) for tag in MANAGED if tag in t.keys()}

    def replace(values):
        for tag in MANAGED:
            if tag in t.keys() and tag not in values:
                del t[tag]
        for tag, value in values.items():
            t[tag] = bytearray(value)

    try:
        replace(decoded)
        fontlab.flItems.notifyFeaturesChanged(p.fgId, True)
        persist(p, compiled_revision=args["revision"], create=True)
        notify(p, "MCP publish compiled OpenType tables")
    except Exception:
        replace(old)
        p.packageLib = before_library
        try:
            fontlab.flItems.notifyFeaturesChanged(p.fgId, True)
        except Exception:
            pass
        raise
    report["persistence"] = (
        "native package-library archive; helper rehydrates raw buffers on access"
    )
    report["stored_tables"] = table_rows(
        {tag: bytes(t[tag]) for tag in MANAGED if tag in t.keys()}
    )
    return report


def font_hinting(p, args):
    kind = args.get("kind", "all")
    if kind not in ("all", "zones", "stems"):
        raise ValueError("kind must be all, zones or stems")
    offset, limit = args.get("offset", 0), args.get("limit", 50)
    if (
        any(
            isinstance(x, bool)
            or not isinstance(x, (int, float))
            or int(x) != x
            or x < 0
            for x in (offset, limit)
        )
        or not 1 <= limit <= 100
    ):
        raise ValueError("Integer offset >=0 and limit 1..100 required")
    master = args.get("master_name", p.master)
    if master not in p.masters:
        raise ValueError("Unknown master")
    before = p.master
    workspace = fontlab.flWorkspace.instance()
    active_before = workspace.currentPackage
    rows = []
    try:
        p.setMaster(master)
        if kind in ("all", "zones"):
            for family, groups in [
                ("postscript", ("ps_zonesT", "ps_zonesB")),
                ("truetype", ("tt_zonesT", "tt_zonesB")),
                ("family", ("family_zonesT", "family_zonesB")),
            ]:
                for side, prop in zip(("top", "bottom"), groups):
                    for z in getattr(p, prop):
                        rows.append(
                            dict(
                                kind="zone",
                                system=family,
                                side=side,
                                name=z.name,
                                position=z.position,
                                width=z.width,
                                tags=z.tags,
                                program=z.programText,
                            )
                        )
        if kind in ("all", "stems"):
            for family, prefix in [("postscript", "ps"), ("truetype", "tt")]:
                for axis, suffix in [("horizontal", "H"), ("vertical", "V")]:
                    for s in getattr(p, prefix + "_stems" + suffix):
                        rows.append(
                            dict(
                                kind="stem",
                                system=family,
                                orientation=axis,
                                name=s.name,
                                value=s.value,
                                tags=s.tags,
                                program=s.programText,
                            )
                        )
    finally:
        p.setMaster(before)
        active_now = workspace.currentPackage
        if active_before is not None and (
            active_now is None or active_now.fgId != active_before.fgId
        ):
            fontlab.SetCurrentFont(active_before.fgPackage)
    selected = []
    size = 0
    for row in rows[int(offset) : int(offset + limit)]:
        count = len(json.dumps(row).encode())
        if count > 40000:
            raise ValueError("Hinting record exceeds response budget")
        if size + count > 40000:
            break
        selected.append(row)
        size += count
    end = int(offset) + len(selected)
    return dict(
        font_id=p.fgId,
        master_name=master,
        masters=list(p.masters),
        records=selected,
        total=len(rows),
        has_more=end < len(rows),
        next_offset=end if end < len(rows) else None,
        source="native stored zones and stems; no autohint or detection",
    )


def dispatch(name, args, p, notify):
    if name == "get_opentype_tables":
        return stored(p, args)
    if name == "compile_features":
        return publish(p, args, notify)
    if name == "get_layer_hints":
        return layer_hints(p, args)
    if name == "get_font_hinting":
        return font_hinting(p, args)
    raise ValueError("Unsupported engineering operation")


def layer_hints(p, args):
    from .glyph_access import resolve

    g, l = resolve(p, args)
    if args.get("include_tth"):
        raise ValueError(
            "TrueType command strings are not qualified; count-only is available"
        )
    offset, limit = args.get("offset", 0), args.get("limit", 50)
    if (
        any(isinstance(x, bool) or int(x) != x for x in (offset, limit))
        or offset < 0
        or not 1 <= limit <= 100
    ):
        raise ValueError("offset >=0 and limit 1..100 required")
    offset, limit = int(offset), int(limit)
    rows = []
    for v in l.guidelines:
        if not v.isHint:
            continue
        vertical = v.isVerticalQuarter
        rows.append(
            dict(
                hint_index=len(rows),
                orientation="vertical" if vertical else "horizontal",
                position=v.centerPoint.x() if vertical else v.centerPoint.y(),
                width=v.extPosition,
                name=v.name,
                has_expression=v.hasExpression,
                passive=v.isPassive,
                ghost=None,
                extended_line=v.hasExtLine,
            )
        )
    selected = []
    size = 0
    for row in rows[offset : offset + limit]:
        count = len(json.dumps(row).encode())
        if count > 40000:
            raise ValueError("Hint record exceeds response budget")
        if size + count > 40000:
            break
        selected.append(row)
        size += count
    end = offset + len(selected)
    return dict(
        font_id=p.fgId,
        glyph_name=g.name,
        layer_name=l.name,
        hints=selected,
        total=len(rows),
        has_more=end < len(rows),
        next_offset=end if end < len(rows) else None,
        tth_command_count=len(l.tthProgram),
        ghost_and_lock_link_decoding_supported=False,
        source="native stored hint guidelines, not detected preview stems",
    )

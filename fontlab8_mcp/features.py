"""Native feature-source exchange; compiled publication remains separate/unported."""

import hashlib
import json
from pathlib import Path


def read(p):
    f = p.fgPackage.features
    text = f.get_prefix()
    for tag in f.keys():
        code = f.get_feature(tag)
        text += "\n" + (
            code
            if code.strip().startswith("feature ")
            else "feature " + tag + " {\n" + code + "\n} " + tag + ";"
        )
    groups = {}
    for name, g in p.fgPackage.groups.asDict().items():
        groups[name] = dict(members=list(g), mode=g.mode)
    order = [g.name for g in p.fgPackage.glyphs]
    revision = hashlib.sha256(
        json.dumps([text, groups, order], sort_keys=True).encode()
    ).hexdigest()
    return dict(
        version=1,
        revision=revision,
        data=dict(text=text),
        shared_classes=groups,
        glyph_order=order,
    )


def dispatch(name, args, p, notify):
    current = read(p)
    if name == "get_features":
        fmt = args.get("format", "json")
        if fmt not in ("json", "fea"):
            raise ValueError("format must be json or fea")
        if fmt == "fea" and "output_path" not in args:
            raise ValueError("fea requires output_path")
        if "output_path" in args:
            path = Path(args["output_path"])
            if not path.is_absolute():
                raise ValueError("Absolute output_path required")
            if path.exists() and not args.get("overwrite"):
                raise ValueError("Output exists")
            text = (
                current["data"]["text"]
                if fmt == "fea"
                else json.dumps(current["data"], indent=2)
            )
            with path.open(
                "w" if args.get("overwrite") else "x", encoding="utf-8"
            ) as out:
                out.write(text)
            current["output_path"] = str(path)
        return current
    if args.get("version") != 1 or args["revision"] != current["revision"]:
        raise ValueError("Stale feature revision or unsupported version; read again")
    data = args.get("data")
    if (
        not isinstance(data, dict)
        or set(data) != {"text"}
        or not isinstance(data["text"], str)
    ):
        raise ValueError("data must contain exactly text:string")
    if len(data["text"].encode()) > 1024 * 1024:
        raise ValueError("Feature text exceeds port limit of 1 MiB")
    if args.get("dry_run"):
        return dict(dry_run=True, revision=current["revision"], undo_supported=False)
    f = p.fgPackage.features
    from .layout_buffer import capture, restore

    previous_tables = capture(p)
    # Native source edits rewrite FG's layout buffers; freeze the previously
    # published bytes until an explicit compile_features publication.
    try:
        for tag in list(f.keys()):
            f.remove(tag)
        f.set_prefix(data["text"])
        import fontlab

        fontlab.flItems.notifyFeaturesChanged(p.fgId, False)
        notify(p, "MCP feature source edit")
    except Exception:
        f.set_prefix(current["data"]["text"])
        raise
    finally:
        restore(p, previous_tables)
    result = read(p)
    result.update(undo_supported=False, compiled_tables_preserved=True)
    return result

"""Native FontLab 8 operations; contracts derive from the shipped FontLab 9 catalog."""

import importlib
import copy
import json
from pathlib import Path
import tempfile
import shutil
import fontlab
import fontgate

SUPPORTED = {
    "list_fonts",
    "get_active_font",
    "set_active_font",
    "open_font",
    "new_font",
    "save_font",
    "close_font",
    "get_font_info",
    "set_font_info",
    "get_font_metrics",
    "set_font_metrics",
    "list_glyphs",
    "get_glyph_metrics",
    "set_glyph_metrics",
    "run_python",
    "get_python_output",
}
from . import capabilities

importlib.reload(capabilities)
from . import layout_buffer

importlib.reload(layout_buffer)
GLYPH_NAMES, FEATURE_NAMES = capabilities.GLYPH_NAMES, capabilities.FEATURE_NAMES
SUPPORTED |= capabilities.ENGINEERING_NAMES
SUPPORTED |= (
    GLYPH_NAMES | FEATURE_NAMES | {"export_font", "get_glyph_info", "set_glyph_info"}
)

from . import extra_tools

importlib.reload(extra_tools)
SUPPORTED |= set(extra_tools.TOOLS)

ALIASES = {
    "family_name": "familyName",
    "style_name": "styleName",
    "upm": "unitsPerEm",
    "x_height": "xHeight",
    "cap_height": "capHeight",
    "italic_angle": "italicAngle",
    "line_gap": "openTypeHheaLineGap",
    "weight": "openTypeOS2WeightClass",
    "width": "openTypeOS2WidthClass",
    "designer": "openTypeNameDesigner",
    "manufacturer": "openTypeNameManufacturer",
    "vendor_id": "openTypeOS2VendorID",
}


def packages():
    return [fontlab.flPackage(obj) for obj in fontlab.flWorkspace.instance().packages()]


def choose(args):
    fonts = packages()
    if "font_id" in args:
        matches = [
            p for p in fonts if p.fgId == args["font_id"] or p.id == args["font_id"]
        ]
    elif "font_name" in args:
        matches = [
            p
            for p in fonts
            if args["font_name"] in [p.title_name(), p.tfn, p.psn, p.ffn]
        ]
    else:
        p = fontlab.flWorkspace.instance().currentPackage
        if p is not None:
            return p
        matches = fonts
    if len(matches) != 1:
        raise ValueError("Select exactly one open font using font_id from list_fonts")
    return matches[0]


def summary(p):
    return dict(
        id=p.fgId,
        family_name=p.tfn,
        style_name=p.tsn,
        full_name=p.ffn,
        postscript_name=p.psn,
        file_name=p.fileName,
        path=p.path,
        upm=p.upm,
        glyph_count=p.glyphsCount,
        masters_count=len(p.masters),
        is_master=p.isMaster,
        is_key=p.isKey,
    )


def fields(p):
    result = {}
    info = p.info
    for key in dir(info):
        if not key.startswith("_"):
            value = getattr(info, key)
            json.dumps(value, allow_nan=False)
            result[key] = value
    return result


def notify(p, title):
    p.update()
    fontlab.flItems.notifyChangesApplied(title, p, True)
    fontlab.Update(p)
    p.setFlag(p.flObjectFlags["ofChanged"], True)


def patch_info(p, args):
    if args.get("scale_upm"):
        raise ValueError(
            "Scaling outlines with UPM is not yet qualified; use scale_upm=false"
        )
    root = copy.deepcopy(args.get("font_info", {}))
    if not isinstance(root, dict):
        raise ValueError("font_info must be an object")
    per_master = root.pop("masters", [])
    plans = []
    original = p.master
    names = list(p.masters)
    targets = names if args.get("all_masters") else [args.get("master_name", original)]
    plans.extend((name, root) for name in targets if root)
    for item in per_master:
        if not isinstance(item, dict) or "name" not in item:
            raise ValueError("Each master patch needs a name")
        plans.append((item["name"], {k: v for k, v in item.items() if k != "name"}))
    known = fields(p)
    prepared = []
    for master, patch in plans:
        if master not in names:
            raise ValueError("Unknown master: " + str(master))
        normalized = {}
        for key, value in patch.items():
            key = ALIASES.get(key, key)
            if key not in known:
                raise ValueError("FontLab 8 has no exposed FontInfo field: " + key)
            json.dumps(value, allow_nan=False)
            if key == "unitsPerEm" and (
                type(value) not in (int, float) or not 16 <= value <= 16384
            ):
                raise ValueError("unitsPerEm must be between 16 and 16384")
            normalized[key] = value
        prepared.append((master, normalized))
    before = []
    try:
        # Snapshot every target before mutation, then restore on a rejected setter.
        for master, patch in prepared:
            p.setMaster(master)
            before.append(
                (master, {k: copy.deepcopy(getattr(p.info, k)) for k in patch})
            )
        for master, patch in prepared:
            p.setMaster(master)
            for key, value in patch.items():
                if key == "unitsPerEm":
                    p.setUpm(int(value), bool(args.get("scale_upm", False)))
                else:
                    setattr(p.info, key, value)
                if getattr(p.info, key) != value:
                    raise ValueError("Native setter did not retain " + key)
        if prepared:
            notify(p, "MCP Font Info")
    except Exception:
        for master, patch in reversed(before):
            p.setMaster(master)
            for key, value in patch.items():
                if key == "unitsPerEm":
                    p.setUpm(int(value), bool(args.get("scale_upm", False)))
                else:
                    setattr(p.info, key, value)
        raise
    finally:
        p.setMaster(original)
    return dict(
        status="ok",
        font=summary(p),
        updated_fields=[dict(master=m, fields=list(patch)) for m, patch in prepared],
    )


def dispatch(name, args):
    if name not in SUPPORTED:
        raise ValueError("FontLab 9 tool not ported/verified for FontLab 8: " + name)
    if name in ("get_classes", "set_classes"):
        from . import classes as module

        importlib.reload(module)
        if name == "get_classes":
            return module.read(choose(args))
        return module.write(choose(args), args, notify)
    if name in ("get_glyph_source", "set_glyph_source"):
        from . import glyph_source as module

        importlib.reload(module)
        if name == "get_glyph_source":
            result = module.read(choose(args), args)
            if args.get("format", "json") == "glif":
                from .glif_exchange import xml_from_source

                result["xml"] = xml_from_source(result["source"])
            return result
        if args.get("format", "json") == "glif":
            if "source" in args or "xml" not in args:
                raise ValueError("GLIF write requires xml only")
            from .glif_exchange import source_from_xml

            snapshot = module.read(choose(args), args)
            args = dict(args, source=source_from_xml(args["xml"], snapshot["source"]))
        elif "source" not in args or "xml" in args:
            raise ValueError("JSON write requires source only")
        return module.write(choose(args), args, notify)
    if name in ("get_font_structure", "set_font_structure"):
        from . import structure as module

        importlib.reload(module)
        if name == "get_font_structure":
            return module.read(choose(args))
        return module.write(choose(args), args, notify)
    if name in ("get_glyph_info", "set_glyph_info"):
        from . import glyph_info as module

        return importlib.reload(module).dispatch(name, args, choose(args), notify)
    if name == "export_font":
        from . import export as module

        return importlib.reload(module).export(choose(args), args)
    if name in FEATURE_NAMES:
        from . import features as module

        return importlib.reload(module).dispatch(name, args, choose(args), notify)
    if name in capabilities.ENGINEERING_NAMES:
        from . import engineering as module

        return importlib.reload(module).dispatch(name, args, choose(args), notify)
    if name in GLYPH_NAMES:
        from . import glyph_access as module

        return importlib.reload(module).dispatch(name, args, choose(args), notify)
    if name == "list_fonts":
        return dict(fonts=[summary(p) for p in packages()])
    if name in ("new_font", "open_font"):
        if name == "new_font":
            if args.get("encoding") not in (None, "Latin Simple"):
                raise ValueError("Alternate display encodings are not yet ported")
            path = Path(tempfile.mkdtemp(prefix="fontlab8-mcp-")) / "NewFont.ufo"
            f = fontgate.fgFont()
            f.info.familyName = args.get("family_name", "Untitled")
            f.info.styleName = args.get("style_name", "Regular")
            f.info.unitsPerEm = 1000
            f.createGlyph(".notdef")
            f.save(str(path))
        else:
            path = Path(args["path"]).expanduser().resolve()
            if not path.exists():
                raise ValueError("Font file does not exist")
        if not fontlab.flWorkspace.instance().mainWindow.loadFont(str(path)):
            raise ValueError("FontLab could not open this file")
        p = choose({})
        if name == "new_font":
            patch_info(
                p,
                dict(
                    font_info=dict(
                        familyName=args.get("family_name", "Untitled"),
                        styleName=args.get("style_name", "Regular"),
                    )
                ),
            )
        return dict(status="ok", font=summary(p))
    p = choose(args)
    if name == "get_active_font":
        return dict(font=summary(p))
    if name == "set_active_font":
        fontlab.SetCurrentFont(p.fgPackage)
        return dict(status="ok", font=summary(p))
    if name == "get_font_info":
        if args.get("detail", "full") != "full":
            raise ValueError("Native named hinting detail is not yet ported")
        original = p.master
        try:
            if "master_name" in args:
                if args["master_name"] not in p.masters:
                    raise ValueError("Unknown master")
                p.setMaster(args["master_name"])
            return dict(
                font=summary(p),
                master_name=p.master,
                masters=list(p.masters),
                font_info=fields(p),
                adapter_note="FontLab 8 native FontInfo fields; response is not arbitrary full VFJ JSON",
            )
        finally:
            p.setMaster(original)
    if name == "set_font_info":
        return patch_info(p, args)
    if name == "get_font_metrics":
        mapping = {
            "upm": "unitsPerEm",
            "ascender": "ascender",
            "descender": "descender",
            "x_height": "xHeight",
            "cap_height": "capHeight",
            "italic_angle": "italicAngle",
            "line_gap": "openTypeHheaLineGap",
            "weight": "openTypeOS2WeightClass",
            "width": "openTypeOS2WidthClass",
        }
        return dict(
            font=summary(p), metrics={k: getattr(p.info, v) for k, v in mapping.items()}
        )
    if name == "set_font_metrics":
        return patch_info(
            p,
            dict(
                font_info={
                    ALIASES.get(k, k): v
                    for k, v in args.items()
                    if k not in ["font_id", "font_name"]
                }
            ),
        )
    if name == "save_font":
        requested_kind = args.get(
            "format", Path(args.get("path") or p.path).suffix.lstrip(".")
        ).lower()
        if requested_kind in ("vfc", "vfj"):
            from . import native_save as module

            return importlib.reload(module).save(p, args, summary)
        if len(p.masters) != 1:
            raise ValueError(
                "UFO snapshot save is restricted to a single master to avoid silently losing family metadata. Native multi-master VFC/VFJ save remains unqualified."
            )
        if not args.get("path"):
            raise ValueError(
                "Supply an explicit new .ufo path; in-place native saving is not qualified"
            )
        path = Path(args["path"]).expanduser().resolve()
        kind = args.get("format", path.suffix.lstrip(".")).lower()
        if kind != "ufo" or path.suffix.lower() != ".ufo":
            raise ValueError(
                "This port currently verifies UFO snapshot saving only. Native VFC/VFJ saving is not qualified; existing VFC/VFJ fonts can still be opened and edited."
            )
        if path.exists():
            raise ValueError("Existing outputs are preserved; choose a new UFO path")
        path.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".mcp-ufo-", dir=str(path.parent)))
        previous = p.fgPackage.path
        try:
            source = staging / "snapshot.ufo"
            p.prepareFontGateData(False)
            p.fgPackage.save(str(source))
            if not (source / "fontinfo.plist").is_file():
                raise ValueError("Native UFO save did not produce fontinfo.plist")
            source.rename(path)
        finally:
            p.fgPackage.path = previous
            shutil.rmtree(staging, ignore_errors=True)
        return dict(
            status="ok",
            font=summary(p),
            path=str(path),
            save_mode="copy",
            note="Native document path is preserved; this writes a UFO snapshot copy",
        )
    if name == "close_font":
        if args.get("save"):
            raise ValueError("Save to an explicit path with save_font before closing")
        if p.hasChanges or p.isChanged:
            raise ValueError(
                "Dirty-font closing is not qualified for headless FontLab 8. The document was left open; close it in FontLab after reviewing/saving. Only clean documents can be closed through this port."
            )
        p.close(False)
        return dict(status="ok")
    if name == "list_glyphs":
        if args.get("detail", "basic") != "basic":
            raise ValueError(
                "Only basic names/unicodes detail is qualified; facts detail is not ported"
            )
        unsupported = set(args) - {
            "font_id",
            "font_name",
            "detail",
            "query",
            "limit",
            "offset",
            "has_unicode",
        }
        if unsupported:
            raise ValueError(
                "Unported glyph fact filters: " + ", ".join(sorted(unsupported))
            )
        rows = []
        for g in p.fgPackage.glyphs:
            if args.get("query", "").lower() not in g.name.lower():
                continue
            unicodes = list(g.unicodes)
            if "has_unicode" in args and bool(unicodes) != args["has_unicode"]:
                continue
            rows.append(dict(name=g.name, unicodes=unicodes))
        offset = max(0, int(args.get("offset", 0)))
        limit = min(200, max(1, int(args.get("limit", 50))))
        return dict(
            glyphs=rows[offset : offset + limit],
            total=len(rows),
            has_more=offset + limit < len(rows),
            next_offset=offset + limit if offset + limit < len(rows) else None,
        )
    if name in ["get_glyph_metrics", "set_glyph_metrics"]:
        from . import metrics

        importlib.reload(metrics)
        matches = [v for v in p.fgPackage.glyphs if v.name == args["glyph_name"]]
        if len(matches) != 1:
            raise ValueError("Exact existing glyph required")
        native = fontlab.flGlyph(matches[0])
        if name == "set_glyph_metrics":
            value = metrics.edit(native, args)
            notify(p, "MCP numeric spacing")
        else:
            value = metrics.read(native)
        return dict(glyph_name=matches[0].name, **value)
    raise ValueError("Unhandled tool: " + name)

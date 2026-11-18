"""Stdio MCP facade using FontLab 9's native tool names and input schemas."""

import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator
from fontTools.ufoLib import validateInfoVersion3Data
from .client import call
from .guidance import GUIDE, URI, INSTRUCTIONS

ROOT = Path(__file__).resolve().parents[1]
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
from .capabilities import GLYPH_NAMES, FEATURE_NAMES, ENGINEERING_NAMES

SUPPORTED |= GLYPH_NAMES | FEATURE_NAMES | ENGINEERING_NAMES | {"export_font"}
CATALOG = json.loads((ROOT / "tool-catalog.json").read_text())["tools"]
TOOLS = {t["name"]: t for t in CATALOG if t["name"] in SUPPORTED}
TOOLS["export_font"] = dict(
    name="export_font",
    description="FontLab 8 extension (not one of the native 9 catalog's 56 names): export using a native profile to a new directory. Interchange may omit FontLab-only data.",
    inputSchema=dict(
        type="object",
        additionalProperties=False,
        required=["format", "directory"],
        properties={
            "font_id": {"type": "number"},
            "font_name": {"type": "string"},
            "format": {
                "enum": ["glyphs", "glyphspackage", "designspace", "ufo", "ttf", "otf"]
            },
            "directory": {"type": "string"},
        },
    ),
)
# Additional FontLab 8 metadata operations; explicitly separate from the native9 catalog.
selector = {"font_id": {"type": "number"}, "font_name": {"type": "string"}}
TOOLS["get_glyph_info"] = dict(
    name="get_glyph_info",
    description="FontLab 8 extension: read notes, color marks, tags and Unicode scalars for named glyphs.",
    inputSchema=dict(
        type="object",
        additionalProperties=False,
        properties=dict(
            selector,
            glyph_names=dict(type="array", maxItems=256, items=dict(type="string")),
        ),
    ),
)
TOOLS["set_glyph_info"] = dict(
    name="set_glyph_info",
    description="FontLab 8 extension: preflight and apply bulk glyph metadata patches; native undo not qualified. Supports explicit new_name; does not rewrite feature/class text references or replace outlines.",
    inputSchema=dict(
        type="object",
        additionalProperties=False,
        required=["edits"],
        properties=dict(
            selector,
            edits=dict(
                type="array",
                minItems=1,
                maxItems=256,
                items=dict(
                    type="object",
                    additionalProperties=False,
                    required=["glyph_name"],
                    properties=dict(
                        glyph_name=dict(type="string"),
                        note=dict(type="string", maxLength=65536),
                        mark=dict(type="integer", minimum=0, maximum=15),
                        tags=dict(
                            type="array",
                            maxItems=128,
                            uniqueItems=True,
                            items=dict(type="string", minLength=1, maxLength=128),
                        ),
                        unicodes=dict(
                            type="array",
                            maxItems=256,
                            uniqueItems=True,
                            items=dict(type="integer", minimum=0, maximum=1114111),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
SUPPORTED |= {"get_glyph_info", "set_glyph_info"}
TOOLS["set_glyph_info"]["inputSchema"]["properties"]["edits"]["items"]["properties"][
    "new_name"
] = {"type": "string", "minLength": 1, "maxLength": 128}
from .extra_tools import TOOLS as EXTRA_TOOLS

TOOLS.update(EXTRA_TOOLS)
SUPPORTED |= set(EXTRA_TOOLS)
LIMITS = {
    "get_font_info": "Returns 96 native FontInfo fields, not full VFJ package JSON; detail=full only. Master selection is supported.",
    "set_font_info": "Native FontInfo field patches and masters[] are supported. scale_upm=true, axes/instances and arbitrary VFJ replacement are not qualified.",
    "save_font": "Native in-place VFC/VFJ save with retained backups; existing files require overwrite=true. First native save requires original basename.vfc and creates a VFJ sidecar. Native Save As to another path is refused. UFO remains a limited single-master snapshot.",
    "close_font": "Clean fonts only. Dirty fonts and save=true are refused without opening a dialog. No forced discard.",
    "new_font": "Only the default Latin Simple repertoire is qualified.",
    "list_glyphs": "Names/unicodes and query/has_unicode pagination only; facts/geometry filters are not ported.",
    "get_glyph_metrics": "Numeric width/LSB/RSB and current expression strings; empty glyph sidebearings are null.",
    "set_glyph_metrics": "Manual numeric width/LSB/RSB. LSB shifts ink and advance together to retain RSB; explicit width/RSB conflicts rejected. Bound expressions and Auto layers refused.",
    "run_python": "Prefer dedicated tools. fgFont has no .fg attribute; do not assume FontLab 9 APIs. Persistent namespace provides fontlab/fontgate; fontpr/mcp_tools expose only the ported subset. Set result to JSON-serializable data. NOT transactional: prior changes survive errors; read back before retrying. Read fontlab8://guide/agent-workflow.",
    "get_python_output": "Only output captured from this adapter’s most recent run_python call, not the entire FontLab Output panel.",
}

LIMITS.update(
    {
        "get_features": "Native source, shared FontGate classes and glyph order with revision. Not native compiled lookup access.",
        "set_features": "Source replacement; external FontTools validation, revision/dry-run. 1 MiB limit; include() refused. Raw layout bytes preserved; native Undo/visual Lookup behavior not qualified.",
        "get_glyph": "detail=construction only: layer flags and anchors; full VFJ/component detail and attachment analysis not ported.",
        "get_glyph_nodes": "Indexed local nodes and transforms; extrema computation not ported.",
        "edit_glyph_nodes": "Coordinate set/move only; preflight/dry-run supported, native undo not qualified. Components and Auto layers refused.",
        "set_glyph_anchors": "Native position/name/remove/expression/cloud fields; mark_enabled and native undo not qualified.",
        "export_font": "Native export profiles into new directory; this is an additional FontLab 8 tool, not a shipped FontLab 9 name.",
    }
)
LIMITS.update(
    {
        "get_opentype_tables": "Reads native runtime table bytes; helper-managed archives rehydrate after native save/reopen. Not fresh export/compilation. Inline data limited to 512 KiB; larger data requires file export.",
        "compile_features": "FontTools feaLib detached compilation via MCP stdio, then raw GSUB/GPOS/GDEF publication with compensation and native package-library archive for persistence. 1 MiB compiled/8 MiB archive limits; additional generated tables refused. Native Undo, visual lookup behavior and fontpr compilation are not qualified.",
        "get_font_hinting": "Reads native PS/TT/family zones and PS/TT stems, per master with pagination. No automatic hinting.",
    }
)
LIMITS["get_layer_hints"] = (
    "Reads native stored PS hint position/width/orientation/name and TTH count. Ghost, lock/link decoding and include_tth command strings are not qualified; no hint detection."
)
LIMITS["set_features"] = (
    "Source replacement with FontTools validation, revision/dry-run and 1 MiB limit; include() refused. Raw layout bytes preserved. Native Undo and visual Lookup state not qualified."
)
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
    "panose": "openTypeOS2Panose",
}


def validate_metadata(args):
    patch = args.get("font_info", {})
    records = [{k: v for k, v in patch.items() if k != "masters"}]
    records.extend(
        {k: v for k, v in master.items() if k != "name"}
        for master in patch.get("masters", [])
    )
    for record in records:
        validateInfoVersion3Data(
            {ALIASES.get(k, k): v for k, v in record.items() if v is not None}
        )


def prepare_features(args):
    args = dict(args)
    if ("data" in args) == ("data_path" in args):
        raise ValueError("Supply exactly one of data or data_path")
    if "data_path" in args:
        path = Path(args.pop("data_path"))
        if not path.is_absolute() or path.stat().st_size > 1024 * 1024:
            raise ValueError("Absolute feature file <=1 MiB required")
        text = path.read_text(encoding="utf-8")
        args["data"] = (
            {"text": text} if args.get("format", "json") == "fea" else json.loads(text)
        )
    data = args["data"]
    if (
        not isinstance(data, dict)
        or set(data) != {"text"}
        or not isinstance(data["text"], str)
    ):
        raise ValueError("data must be exactly text:string")
    if len(data["text"].encode()) > 1024 * 1024:
        raise ValueError("Feature source exceeds 1 MiB")
    if args.get("validate", True):
        import re

        if re.search(r"\binclude\s*\(", data["text"]):
            raise ValueError(
                "include() is not supported; provide self-contained source"
            )
        snapshot = call(
            "get_features",
            {k: v for k, v in args.items() if k in ("font_id", "font_name")},
        )
        if snapshot["revision"] != args["revision"]:
            raise ValueError("Stale feature revision")
        from fontTools.ttLib import TTFont
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

        candidate = TTFont()
        candidate.setGlyphOrder(snapshot["glyph_order"])
        text = data["text"]
        prefix = ""
        for name, group in snapshot.get("shared_classes", {}).items():
            if group["mode"] == "FeaClassGroupMode" and not re.search(
                "@" + re.escape(name) + r"\s*=", text
            ):
                # Native class names/glyph names are escaped FEA identifiers.
                prefix += (
                    "@"
                    + name
                    + " = ["
                    + " ".join("\\" + glyph for glyph in group["members"])
                    + "];\n"
                )
        addOpenTypeFeaturesFromString(candidate, prefix + text)
    return args


def handle(request):
    ident = request.get("id")
    if "id" not in request:
        return None
    try:
        method = request.get("method")
        if method == "initialize":
            result = dict(
                protocolVersion="2024-11-05",
                capabilities={"tools": {"listChanged": False}, "resources": {}, "prompts": {}},
                instructions=INSTRUCTIONS,
                serverInfo={"name": "Unofficial MCP Adapter for FontLab 8", "version": "0.4.1"},
            )
        elif method == "resources/list":
            result = {"resources": [{"uri": URI, "name": "FontLab 8 agent workflow", "mimeType": "text/plain", "description": "Python object boundaries, dedicated tools and persistence verification."}]}
        elif method == "resources/read":
            if request.get("params", {}).get("uri") != URI:
                raise ValueError("Unknown resource URI")
            result = {"contents": [{"uri": URI, "mimeType": "text/plain", "text": GUIDE}]}
        elif method == "prompts/list":
            result = {"prompts": [{"name": "fontlab8-workflow", "description": "Use FontLab 8 tools without assuming FontLab 9 Python APIs."}]}
        elif method == "prompts/get":
            if request.get("params", {}).get("name") != "fontlab8-workflow":
                raise ValueError("Unknown prompt")
            result = {"description": "FontLab 8 editing workflow", "messages": [{"role": "user", "content": {"type": "text", "text": GUIDE}}]}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {
                "tools": [
                    dict(
                        t,
                        description="FontLab 8 port: "
                        + LIMITS.get(t["name"], "Verified basic native operation.")
                        + (
                            " FontLab 9 reference contract: "
                            if t["name"] in {x["name"] for x in CATALOG}
                            else " Additional FontLab 8 contract: "
                        )
                        + t["description"],
                    )
                    for t in TOOLS.values()
                ]
            }
        elif method == "tools/call":
            params = request["params"]
            name = params["name"]
            args = params.get("arguments", {})
            if name not in TOOLS:
                raise ValueError("Tool is not ported/advertised: " + name)
            Draft202012Validator(TOOLS[name]["inputSchema"]).validate(args)
            if name == "set_font_info":
                validate_metadata(args)
            elif name == "set_font_metrics":
                validate_metadata(
                    {
                        "font_info": {
                            k: v
                            for k, v in args.items()
                            if k not in ["font_id", "font_name"]
                        }
                    }
                )
            if name == "set_features":
                args = prepare_features(args)
            if name == "compile_features":
                from .compiler import prepare

                args = prepare(args, call)
            value = call(name, args)
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(value, ensure_ascii=False, allow_nan=False),
                    }
                ]
            }
        else:
            return dict(
                jsonrpc="2.0",
                id=ident,
                error=dict(code=-32601, message="Method not found"),
            )
        return dict(jsonrpc="2.0", id=ident, result=result)
    except Exception as exc:
        if request.get("method") == "tools/call":
            return dict(
                jsonrpc="2.0",
                id=ident,
                result=dict(isError=True, content=[dict(type="text", text=str(exc))]),
            )
        return dict(jsonrpc="2.0", id=ident, error=dict(code=-32602, message=str(exc)))


def main():
    for line in sys.stdin.buffer:
        try:
            if len(line) > 2 * 1024 * 1024:
                raise ValueError("MCP frame exceeds 2 MiB")
            request = json.loads(
                line,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    ValueError("Nonfinite JSON")
                ),
            )
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
                raise ValueError("Invalid JSON-RPC request")
            response = handle(request)
        except Exception as exc:
            response = dict(
                jsonrpc="2.0", id=None, error=dict(code=-32700, message=str(exc))
            )
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()

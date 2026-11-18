"""Host-only detached OpenType compilation using mature FontTools."""

import base64, io, logging, re
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString


def compile_snapshot(snapshot):
    text = snapshot["data"]["text"]
    if re.search(r"\binclude\s*\(", text):
        raise ValueError("include() is not supported; supply self-contained source")
    prefix = ""
    for name, group in snapshot.get("shared_classes", {}).items():
        if group["mode"] == "FeaClassGroupMode" and not re.search(
            "@" + re.escape(name) + r"\s*=", text
        ):
            prefix += (
                "@"
                + name
                + " = ["
                + " ".join("\\" + g for g in group["members"])
                + "];\n"
            )
    text = prefix + text
    if re.search(r"\binclude\s*\(", text):
        raise ValueError("include() in class/source data is not supported")
    candidate = TTFont()
    candidate.setGlyphOrder(snapshot["glyph_order"])
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger("fontTools.feaLib")
    logger.addHandler(handler)
    try:
        addOpenTypeFeaturesFromString(candidate, text)
        extra = set(candidate.keys()) - {"GlyphOrder", "GDEF", "GPOS", "GSUB"}
        if extra:
            raise ValueError(
                "Publication of additional tables is not qualified: "
                + ", ".join(sorted(extra))
            )
        data = {
            tag: candidate.getTableData(tag)
            for tag in ("GDEF", "GPOS", "GSUB")
            if tag in candidate
        }
    finally:
        logger.removeHandler(handler)
    return data, output.getvalue().splitlines()


def prepare(args, call):
    snapshot = call(
        "get_features", {k: v for k, v in args.items() if k in ("font_id", "font_name")}
    )
    if snapshot["revision"] != args["revision"]:
        raise ValueError("Stale feature revision")
    data, warnings = compile_snapshot(snapshot)
    if sum(map(len, data.values())) > 1024 * 1024:
        raise ValueError("Compiled publication limit is 1 MiB")
    return dict(
        args,
        compiled_tables={
            tag: base64.b64encode(value).decode() for tag, value in data.items()
        },
        compiler_warnings=warnings,
    )

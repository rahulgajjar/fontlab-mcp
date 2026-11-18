"""Last-published byte cache with explicit native package-library persistence."""

import base64, hashlib

TAGS = ("GDEF", "GPOS", "GSUB")
ARCHIVE = "org.fontcraft.fontlab8-mcp.storedTables.v1"
MAX_BYTES = 8 * 1024 * 1024


def raw(p):
    return {tag: bytes(p.fgPackage.tables[tag]) for tag in p.fgPackage.tables.keys()}


def hydrate(p):
    archive = p.packageLib.get(ARCHIVE)
    if not archive:
        return "native-runtime"
    if archive.get("version") != 1:
        raise ValueError("Unsupported MCP stored-table archive version")
    if raw(p):
        return "native-runtime-with-project-archive"
    if list(archive.get("glyph_order", ())) != [g.name for g in p.fgPackage.glyphs]:
        raise ValueError(
            "Stored-table archive glyph order differs; recompile before restoring tables"
        )
    encoded = archive.get("tables", {})
    if sum(len(v) for v in encoded.values()) > MAX_BYTES * 2:
        raise ValueError("Stored-table archive exceeds size limit")
    data = {
        tag: base64.b64decode(value, validate=True) for tag, value in encoded.items()
    }
    if sum(map(len, data.values())) > MAX_BYTES:
        raise ValueError("Stored-table archive exceeds size limit")
    for tag, value in data.items():
        if (
            not isinstance(tag, str)
            or len(tag) != 4
            or hashlib.sha256(value).hexdigest() != archive.get("sha256", {}).get(tag)
        ):
            raise ValueError("Invalid stored-table archive entry")
    for tag, value in data.items():
        p.fgPackage.tables[tag] = bytearray(value)
    return "rehydrated-from-native-package-library"


def capture(p):
    hydrate(p)
    t = p.fgPackage.tables
    return {tag: bytes(t[tag]) for tag in TAGS if tag in t.keys()}


def restore(p, values):
    t = p.fgPackage.tables
    for tag in TAGS:
        if tag in t.keys() and tag not in values:
            del t[tag]
    for tag, value in values.items():
        t[tag] = bytearray(value)


def persist(p, compiled_revision=None, create=False):
    library = dict(p.packageLib)
    old = library.get(ARCHIVE)
    if old is None and not create:
        return
    hydrate(p)
    if (
        old
        and compiled_revision is None
        and list(old.get("glyph_order", ())) != [g.name for g in p.fgPackage.glyphs]
    ):
        raise ValueError(
            "Archived compiled glyph order changed; explicitly recompile before saving this archived state"
        )
    data = raw(p)
    if sum(map(len, data.values())) > MAX_BYTES:
        raise ValueError("Stored-table archive exceeds 8 MiB")
    if compiled_revision is None and old:
        same = all(
            hashlib.sha256(data[tag]).hexdigest() == old.get("sha256", {}).get(tag)
            for tag in TAGS
            if tag in data
        ) and {t for t in data if t in TAGS} == {
            t for t in old.get("tables", {}) if t in TAGS
        }
        compiled_revision = old.get("compiled_revision") if same else None
    library[ARCHIVE] = dict(
        version=1,
        glyph_order=[g.name for g in p.fgPackage.glyphs],
        compiled_revision=compiled_revision,
        tables={tag: base64.b64encode(value).decode() for tag, value in data.items()},
        sha256={tag: hashlib.sha256(value).hexdigest() for tag, value in data.items()},
    )
    p.packageLib = library

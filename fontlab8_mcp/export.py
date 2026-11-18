"""FontLab 8 extension: native profile export into a new isolated directory."""

from pathlib import Path
import tempfile
import shutil
import fontlab

PROFILES = {
    "glyphs": ("Glyphs", ".glyphs"),
    "glyphspackage": ("Glyphs Package", ".glyphspackage"),
    "designspace": ("DesignSpace + UFO", ".designspace"),
    "ufo": ("UFO Package", ".ufo"),
    "ttf": ("OpenType TT", ".ttf"),
    "otf": ("OpenType PS", ".otf"),
}


def export(p, args):
    kind = args["format"]
    profile, suffix = PROFILES[kind]
    dest = Path(args["directory"]).expanduser()
    if not dest.is_absolute():
        raise ValueError("Absolute destination directory required")
    if dest.exists():
        raise ValueError("Use a new output directory; existing outputs are preserved")
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".mcp-export-", dir=str(dest.parent)))
    try:
        c = fontlab.ExportControl()
        c.profileName = profile
        if c.profileId < 0 or c.profileName != profile:
            raise ValueError("Native profile unavailable: " + profile)
        c.destinationMode = 3
        c.destinationFolder = str(staging)
        c.contentMode = 0
        c.groupFamily = False
        c.groupProfiles = False
        c.conflictMode = 0
        fontlab.flWorkspace.instance().exportFont(p, c)
        outputs = list(staging.rglob("*" + suffix))
        if not outputs:
            raise RuntimeError("Native exporter produced no " + suffix + " output")
        normalized = 0
        if kind == "designspace":
            # FL8 emits <location/> with no axes for a single design. FontTools
            # rejects that redundant element. Preserve raw XML and remove only
            # empty locations when there are no axis declarations.
            import xml.etree.ElementTree as ET

            for output in outputs:
                tree = ET.parse(output)
                root = tree.getroot()
                if not root.findall("./axes/axis"):
                    for parent in root.iter():
                        for location in list(parent):
                            if (
                                location.tag == "location"
                                and not list(location)
                                and not location.attrib
                            ):
                                if not normalized:
                                    shutil.copy2(
                                        output, output.with_suffix(".native.xml")
                                    )
                                parent.remove(location)
                                normalized += 1
                    if normalized:
                        tree.write(output, encoding="utf-8", xml_declaration=True)
        staging.rename(dest)
        return dict(
            status="ok",
            format=kind,
            profile=profile,
            directory=str(dest),
            normalized_empty_locations=normalized,
            files=[str(dest / f.relative_to(staging)) for f in outputs],
            note="Native export profile; format-specific interchange can lose FontLab-only editing data",
        )
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

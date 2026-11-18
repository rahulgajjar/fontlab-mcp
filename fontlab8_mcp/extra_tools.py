"""Explicit FontLab 8 extensions, separate from the 56 native9 reference tools."""

SELECTOR = {"font_id": {"type": "number"}, "font_name": {"type": "string"}}
GLYPH = dict(SELECTOR, glyph_name={"type": "string"}, layer_name={"type": "string"})


def tool(name, description, properties, required=()):
    return dict(
        name=name,
        description="FontLab 8 extension: " + description,
        inputSchema=dict(
            type="object",
            additionalProperties=False,
            properties=properties,
            required=list(required),
        ),
    )


TOOLS = {
    "get_glyph_source": tool(
        "get_glyph_source",
        "Read all existing layer points/anchors/width as native JSON or GLIF XML. Not a full FontLab document serializer.",
        dict(GLYPH, format={"enum": ["json", "glif"]}),
        ["glyph_name"],
    ),
    "set_glyph_source": tool(
        "set_glyph_source",
        "Write layer coordinates, width and anchors from JSON or GLIF; revision required. Existing shape/contour/node topology, types and smooth flags must remain unchanged; no native undo.",
        dict(
            GLYPH,
            format={"enum": ["json", "glif"]},
            source={"type": "object"},
            xml={"type": "string", "maxLength": 1048576},
            revision={"type": "string"},
            dry_run={"type": "boolean"},
        ),
        ["glyph_name", "revision"],
    ),
    "get_font_structure": tool(
        "get_font_structure",
        "Read native axes, master locations and instance metadata with revision. Locations enumerate known axis short names only.",
        SELECTOR,
    ),
}
axis = dict(
    type="object",
    additionalProperties=False,
    required=["short_name"],
    properties={
        k: {"type": typ}
        for k, typ in [
            ("name", "string"),
            ("tag", "string"),
            ("short_name", "string"),
            ("minimum", "number"),
            ("default", "number"),
            ("maximum", "number"),
            ("design_minimum", "number"),
            ("design_default", "number"),
            ("design_maximum", "number"),
            ("hidden", "boolean"),
            ("map", "object"),
        ]
    },
)
inst = dict(
    type="object",
    additionalProperties=False,
    required=["name"],
    properties={
        k: {"type": typ}
        for k, typ in [
            ("name", "string"),
            ("tsn", "string"),
            ("sgn", "string"),
            ("bold", "boolean"),
            ("italic", "boolean"),
            ("exportable", "boolean"),
            ("weight", "string"),
            ("width", "string"),
            ("weightValue", "number"),
            ("slv", "integer"),
            ("location", "object"),
        ]
    },
)
TOOLS["set_font_structure"] = tool(
    "set_font_structure",
    "Patch/add axes and master locations; instances[] replaces the instance list. Revision/preflight/dry-run; native undo and rollback of axis insertion are not qualified.",
    dict(
        SELECTOR,
        revision={"type": "string"},
        axes=dict(type="array", maxItems=32, items=axis),
        master_locations={"type": "object"},
        instances=dict(type="array", maxItems=1024, items=inst),
        dry_run={"type": "boolean"},
    ),
    ["revision"],
)

TOOLS["get_classes"] = tool(
    "get_classes",
    "Read native OpenType class memberships plus native panel summary; kerning class editing is excluded.",
    SELECTOR,
)
TOOLS["set_classes"] = tool(
    "set_classes",
    "Patch/create/remove OpenType class memberships by name, with revision and dry-run. No native undo; nonzero class marks and kerning groups are refused.",
    dict(
        SELECTOR,
        revision={"type": "string"},
        dry_run={"type": "boolean"},
        edits=dict(
            type="array",
            minItems=1,
            maxItems=256,
            items=dict(
                type="object",
                additionalProperties=False,
                required=["name"],
                properties=dict(
                    name={"type": "string"},
                    glyph_names=dict(
                        type="array",
                        minItems=1,
                        maxItems=65536,
                        items={"type": "string"},
                    ),
                    remove={"type": "boolean"},
                ),
            ),
        ),
    ),
    ["revision", "edits"],
)

"""Native axes/master locations and instance metadata exchange."""

import hashlib, json, math, re
import fontlab

AXIS_FIELDS = {
    "name": "name",
    "tag": "tag",
    "short_name": "shortName",
    "minimum": "minimal",
    "default": "default",
    "maximum": "maximum",
    "design_minimum": "designMin",
    "design_default": "designDef",
    "design_maximum": "designMax",
    "hidden": "hidden",
    "map": "map",
}
INSTANCE_FIELDS = [
    "name",
    "tsn",
    "sgn",
    "bold",
    "italic",
    "exportable",
    "weight",
    "width",
    "weightValue",
    "slv",
]


def location(value, axes):
    return {
        a.shortName: value[a.shortName] for a in axes if value[a.shortName] is not None
    }


def read(p):
    axes = list(p.axes)
    data = dict(
        axes=[
            {key: getattr(a, prop) for key, prop in AXIS_FIELDS.items()} for a in axes
        ],
        masters=[
            dict(name=name, location=location(p.location(name), axes))
            for name in p.masters
        ],
        instances=[
            dict(
                **{k: getattr(i, k) for k in INSTANCE_FIELDS},
                location=location(i.location, axes),
            )
            for i in p.instances
        ],
    )
    revision = hashlib.sha256(
        json.dumps(data, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    return dict(
        version=1,
        revision=revision,
        data=data,
        location_key_convention="native axis short_name; arbitrary unknown location keys are not enumerated",
    )


def write(p, args, notify):
    current = read(p)
    if args["revision"] != current["revision"]:
        raise ValueError("Stale structure revision")
    axes_by = {a.shortName: a for a in p.axes}
    used_tags = {a.tag for a in axes_by.values()}
    planned = []
    seen = set()
    for patch in args.get("axes", []):
        key = patch["short_name"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,15}", key):
            raise ValueError("Invalid native axis short_name")
        if key in seen:
            raise ValueError("Duplicate axis short_name")
        seen.add(key)
        if key in axes_by:
            old = axes_by[key]
            if any(
                k in patch and patch[k] != getattr(old, AXIS_FIELDS[k])
                for k in ("tag", "name")
            ):
                raise ValueError("Axis identity rename is not qualified")
            data = {k: getattr(old, v) for k, v in AXIS_FIELDS.items()}
            data.update(patch)
        else:
            if not {"name", "tag"} <= set(patch):
                raise ValueError("New axis requires name/tag/short_name")
            if (
                len(patch["tag"]) != 4
                or any(not 32 <= ord(c) <= 126 for c in patch["tag"])
                or patch["tag"] in used_tags
            ):
                raise ValueError("Axis tag must be unique four characters")
            if not patch["name"].strip() or len(patch["name"]) > 128:
                raise ValueError("Axis name required")
            used_tags.add(patch["tag"])
            base = fontlab.flAxis(patch["name"], patch["tag"], key)
            data = {k: getattr(base, v) for k, v in AXIS_FIELDS.items()}
            data.update(patch)
        for triplet in [
            ("minimum", "default", "maximum"),
            ("design_minimum", "design_default", "design_maximum"),
        ]:
            vals = [data[k] for k in triplet]
            if (
                any(
                    isinstance(v, bool)
                    or not isinstance(v, (int, float))
                    or not math.isfinite(v)
                    for v in vals
                )
                or not vals[0] <= vals[1] <= vals[2]
            ):
                raise ValueError("Axis ranges must be finite and ordered")
        candidate = fontlab.flAxis(data["name"], data["tag"], data["short_name"])
        for k, v in AXIS_FIELDS.items():
            if k == "map":
                mapped = {float(x): float(y) for x, y in data[k].items()}
                if len(mapped) != len(data[k]) or any(
                    not math.isfinite(x) or not math.isfinite(y)
                    for x, y in mapped.items()
                ):
                    raise ValueError("Axis map must contain unique finite coordinates")
                setattr(candidate, v, mapped)
            elif k not in ("name", "tag", "short_name"):
                setattr(candidate, v, data[k])
        planned.append((key, candidate, key not in axes_by))
    valid_axes = set(axes_by) | seen

    def make_location(values):
        if set(values) - valid_axes:
            raise ValueError("Location contains unknown axis short_name")
        out = {}
        for key, value in values.items():
            nums = value if isinstance(value, (tuple, list)) else [value]
            if len(nums) not in (1, 2) or any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                for v in nums
            ):
                raise ValueError("Location requires finite scalar or anisotropic pair")
            out[key] = tuple(nums) if len(nums) == 2 else nums[0]
        return fontlab.flLocation(out)

    locations = []
    for name, values in args.get("master_locations", {}).items():
        if name not in p.masters:
            raise ValueError("Unknown master")
        merged = location(p.location(name), list(p.axes))
        merged.update(values)
        locations.append((name, make_location(merged)))
    instances = []
    names = set()
    for record in args.get("instances", []):
        if not record["name"].strip() or len(record["name"]) > 128:
            raise ValueError("Instance name required")
        if record["name"] in names:
            raise ValueError("Duplicate instance name")
        names.add(record["name"])
        item = fontlab.flInstance(
            record["name"],
            record.get("tsn", record["name"]),
            make_location(record.get("location", {})),
        )
        for field in INSTANCE_FIELDS:
            if field in record:
                setattr(item, field, record[field])
        instances.append(item)
    if args.get("dry_run"):
        return dict(dry_run=True, revision=current["revision"])
    # Native axis insertion has no qualified removal/undo path. Preflight above
    # is complete; a native execution error requires inspection, not replay.
    for key, axis, create in planned:
        if create:
            p.addAxis(axis)
        else:
            p.setAxis(axis)
    for name, value in locations:
        p.setLocation(value, name)
    if "instances" in args:
        p.clearInstances()
        for item in instances:
            p.addInstance(item)
    notify(p, "MCP font structure edit")
    result = read(p)
    result["undo_supported"] = False
    result["previous"] = current["data"]
    return result

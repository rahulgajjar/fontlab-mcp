"""Render the public, project-authored compatibility table."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "comparison.json").read_text())


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


summary = f"**{data['available_native_names']}/56 reference names available with scoped coverage + {data['additional_tools']} additional tools = {data['advertised_tools']} advertised calls.**"
table = "| Tool | Origin | Purpose | Availability | Scope / limit |\n|---|---|---|---|---|\n"
for row in data["tools"]:
    table += (
        "| `"
        + row["name"]
        + "` | "
        + " | ".join(cell(row[k]) for k in ("origin", "purpose", "status", "scope"))
        + " |\n"
    )
p = ROOT / "README.md"
text = p.read_text()
begin = "<!-- BEGIN PUBLIC COMPARISON -->"
end = "<!-- END PUBLIC COMPARISON -->"
a = text.index(begin) + len(begin)
b = text.index(end, a)
p.write_text(text[:a] + "\n\n" + summary + "\n\n" + table + "\n" + text[b:])

"""Render the public, project-authored compatibility table."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "comparison.json").read_text())


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


summary = f"**This adapter offers {data['advertised_tools']} tools: {data['available_native_names']} share names with tools in FontLab 9 MCP, and {data['additional_tools']} are additional adapter tools.**"
table = "| Tool | Purpose | FontLab 9 MCP catalog | This FontLab 8 adapter | Adapter coverage / limitations |\n|---|---|---|---|---|\n"
for row in sorted(data["tools"], key=lambda row: row["status"] != "Available, scoped"):
    listed = "Listed" if row["origin"] == "FontLab 9 name" else "Not in compared catalog"
    status = "Supported, with limits" if row["status"] == "Available, scoped" else "Not supported"
    table += "| `" + row["name"] + "` | " + " | ".join(cell(v) for v in (row["purpose"], listed, status, row["scope"])) + " |\n"
p = ROOT / "README.md"
text = p.read_text()
begin = "<!-- BEGIN PUBLIC COMPARISON -->"
end = "<!-- END PUBLIC COMPARISON -->"
a = text.index(begin) + len(begin)
b = text.index(end, a)
p.write_text(text[:a] + "\n\n" + summary + "\n\n" + table + "\n" + text[b:])

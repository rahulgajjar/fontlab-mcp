from pathlib import Path
import re

from fontlab8_mcp import __version__, server


def test_initialize_reports_version_documented_in_changelog():
    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}

    response = server.handle(request)

    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    release_heading = re.search(r"^## v([^\s]+)", changelog.read_text(encoding="utf-8"), re.M)

    assert release_heading is not None
    assert response["result"]["serverInfo"]["version"] == __version__
    assert release_heading.group(1) == __version__

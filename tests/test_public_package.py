import importlib.util
import json
from pathlib import Path
from fontlab8_mcp import server

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(
        "public_" + name, ROOT / (name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_comparison_and_catalog_match_actual_tools():
    data = json.loads((ROOT / "comparison.json").read_text())
    rows = data["tools"]
    native = {r["name"] for r in rows if r["origin"] == "FontLab 9 name"}
    available = {r["name"] for r in rows if r["status"] == "Available, scoped"}
    assert len(native) == 56 and len(rows) == 65 and len(available) == 35
    assert available == set(server.TOOLS)
    assert len(server.CATALOG) == 26
    assert all(
        "description" not in prop
        for t in server.CATALOG
        for prop in t["inputSchema"].get("properties", {}).values()
    )
    text = (ROOT / "README.md").read_text()
    assert all("| `" + r["name"] + "` |" in text for r in rows)


def test_installer_and_disable_preserve_user_script(tmp_path):
    installer = module("install")
    uninstaller = module("uninstall")
    profile = tmp_path / "profile"
    data = tmp_path / "data"
    profile.mkdir()
    init = profile / "initScript.py"
    init.write_text('# existing user script\nprint("keep")\n')
    first = installer.install(profile, data)
    assert installer.BEGIN in init.read_text() and 'print("keep")' in init.read_text()
    assert (data / "plugin/fontlab8_mcp/runtime.py").is_file()
    assert (
        Path(first["init_backup"]).read_text()
        == '# existing user script\nprint("keep")\n'
    )
    installer.install(profile, data)
    assert init.read_text().count(installer.BEGIN) == 1
    uninstaller.disable(profile)
    assert (
        installer.BEGIN not in init.read_text() and 'print("keep")' in init.read_text()
    )
    assert first["bundle_modified"] is False


def test_malformed_markers_stop_before_writes(tmp_path):
    installer = module("install")
    profile = tmp_path / "profile"
    profile.mkdir()
    init = profile / "initScript.py"
    text = installer.BEGIN + "\nunfinished\n"
    init.write_text(text)
    import pytest

    with pytest.raises(ValueError):
        installer.install(profile, tmp_path / "data")
    assert init.read_text() == text and not (tmp_path / "data").exists()


def test_publication_check():
    spec = importlib.util.spec_from_file_location(
        "public_check", ROOT / "scripts/check_public_tree.py"
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    assert checker.check() == []

"""Install the adapter in a FontLab 8 macOS user profile; never alter the app."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
BEGIN = "# BEGIN FONTLAB8_NATIVE_MCP"
END = "# END FONTLAB8_NATIVE_MCP"


def remove_owned_block(text):
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ValueError(
            "Malformed/duplicate MCP startup markers; initScript.py was not changed"
        )
    if BEGIN not in text:
        return text
    first, last = text.index(BEGIN), text.index(END)
    if last < first:
        raise ValueError("Malformed MCP startup markers; initScript.py was not changed")
    return text[:first] + text[last + len(END) :]


def install(profile, data, source=ROOT):
    profile, data, source = Path(profile), Path(data), Path(source)
    init = profile / "initScript.py"
    original = init.read_text() if init.exists() else ""
    preserved = remove_owned_block(original)  # Preflight before writes.
    if not (source / "fontlab8_mcp/runtime.py").is_file():
        raise ValueError("Run the installer from a complete checkout")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    backups = data / "backups" / stamp
    backups.mkdir(parents=True, mode=0o700)
    profile.mkdir(parents=True, exist_ok=True)
    if init.exists():
        shutil.copy2(init, backups / "initScript.py")
    plugin = data / "plugin"
    if (plugin / "fontlab8_mcp").exists():
        shutil.copytree(plugin / "fontlab8_mcp", backups / "fontlab8_mcp")
    plugin.mkdir(exist_ok=True, mode=0o700)
    shutil.copytree(
        source / "fontlab8_mcp",
        plugin / "fontlab8_mcp",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    start = data / "Start Native FontLab 8 MCP.py"
    start.write_text(
        "#FLM: Start Native FontLab 8 MCP\nimport sys\n_path="
        + repr(str(plugin))
        + "\nif _path not in sys.path: sys.path.insert(0,_path)\n"
        + "from fontlab8_mcp.runtime import start\nstart()\n"
    )
    init.write_text(
        preserved.rstrip()
        + "\n\n"
        + BEGIN
        + "\nexec(compile(open("
        + repr(str(start))
        + ').read(), "FontLab8MCP-init", "exec"))\n'
        + END
        + "\n"
    )
    scripts = profile / "Scripts"
    scripts.mkdir(exist_ok=True)
    shutil.copy2(start, scripts / start.name)
    manifest = dict(
        installed_at=stamp,
        profile=str(profile),
        plugin=str(plugin),
        init_backup=str(backups / "initScript.py"),
        bundle_modified=False,
        sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (source / "fontlab8_mcp").glob("*.py")
        },
    )
    (data / "installation.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    if sys.platform != "darwin":
        raise SystemExit(
            "This installer currently supports macOS only. Platform-port contributions are welcome."
        )
    print(
        json.dumps(
            install(
                Path.home() / "Library/Application Support/FontLab/FontLab 8",
                Path.home() / "Library/Application Support/FontLab8MCP",
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Disable this adapter's startup hook; retain recovery backups."""

from pathlib import Path
import sys
from install import remove_owned_block


def disable(profile):
    path = Path(profile) / "initScript.py"
    if path.exists():
        original = path.read_text()
        updated = remove_owned_block(original)
        if updated != original:
            path.write_text(updated)


if __name__ == "__main__":
    if sys.platform != "darwin":
        raise SystemExit("The current installer/uninstaller supports macOS only.")
    disable(Path.home() / "Library/Application Support/FontLab/FontLab 8")
    print(
        "Startup hook disabled. Restart FontLab when documents are safely saved. Backups and plugin files were retained."
    )

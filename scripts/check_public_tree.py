"""Check that the public tree contains no local research or private paths."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", "local-test-output"}
FORBIDDEN_DIRS = {"research", "evidence", "artifacts"}
FONT_SUFFIXES = {
    ".vfc",
    ".vfj",
    ".vfb",
    ".vfjp",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".glyphs",
    ".ips",
}


def check(root=ROOT):
    failures = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in SKIP for part in relative.parts):
            continue
        if path.is_symlink():
            failures.append(str(relative) + ": unexpected symlink")
            continue
        if any(part in FORBIDDEN_DIRS for part in relative.parts):
            failures.append(str(relative) + ": excluded material")
            continue
        if not path.is_file():
            continue
        if (
            path.name == "native-fontlab9-tools.json"
            or "decompiled" in path.name.lower()
        ):
            failures.append(str(relative) + ": excluded reference/research artifact")
            continue
        if path.suffix.lower() in FONT_SUFFIXES:
            failures.append(str(relative) + ": font/diagnostic artifact")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(str(relative) + ": unexpected binary")
            continue
        if re.search(r"/(?:Users|home)/[^\s/]+/", text):
            failures.append(str(relative) + ": machine-specific home path")
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
            failures.append(str(relative) + ": private-key marker")
        if re.search(r"\bsk-[A-Za-z0-9]{24,}\b", text):
            failures.append(str(relative) + ": possible API credential")
    return failures


if __name__ == "__main__":
    errors = check()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Public tree check passed")

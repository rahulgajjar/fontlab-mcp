"""Optional native smoke test; never uses production fonts or desktop automation."""

import argparse
import json
from pathlib import Path
import select
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def run():
    output = ROOT / "local-test-output" / uuid.uuid4().hex[:10]
    output.mkdir(parents=True)
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "run.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    request_id = 0
    previous = None

    def request(method, params):
        nonlocal request_id
        request_id += 1
        process.stdin.write(
            json.dumps(dict(jsonrpc="2.0", id=request_id, method=method, params=params))
            + "\n"
        )
        process.stdin.flush()
        if not select.select([process.stdout], [], [], 40)[0]:
            raise TimeoutError("Outcome unknown; do not automatically replay a write")
        response = json.loads(process.stdout.readline())
        if "error" in response:
            raise RuntimeError(response["error"])
        return response["result"]

    def call(name, args=None):
        response = request("tools/call", dict(name=name, arguments=args or {}))
        if response.get("isError"):
            raise RuntimeError(response["content"][0]["text"])
        return json.loads(response["content"][0]["text"])

    try:
        request("initialize", {})
        fonts = call("list_fonts")["fonts"]
        if fonts:
            previous = call("get_active_font")["font"]["id"]
        created = call(
            "new_font", dict(family_name="MCP Disposable Smoke", style_name="Regular")
        )["font"]
        ident = created["id"]
        call(
            "set_font_info",
            dict(
                font_id=ident,
                font_info=dict(
                    openTypeNameDesigner="MCP smoke fixture", versionMinor=7
                ),
            ),
        )
        call(
            "set_glyph_metrics",
            dict(font_id=ident, glyph_name=".notdef", advance_width=650),
        )
        path = output / (Path(created["file_name"]).stem + ".vfc")
        call("save_font", dict(font_id=ident, path=str(path.resolve()), format="vfc"))
        clone = output / "reopened.vfc"
        shutil.copy2(path, clone)
        reopened = call("open_font", dict(path=str(clone.resolve())))["font"]["id"]
        assert (
            call("get_font_info", dict(font_id=reopened))["font_info"][
                "openTypeNameDesigner"
            ]
            == "MCP smoke fixture"
        )
        assert (
            call("get_glyph_metrics", dict(font_id=reopened, glyph_name=".notdef"))[
                "advance_width"
            ]
            == 650
        )
        print("Native smoke test passed. Disposable files: " + str(output))
    finally:
        if previous is not None:
            try:
                call("set_active_font", dict(font_id=previous))
            except Exception:
                pass
        process.stdin.close()
        process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live with FontLab 8 running and documents safely saved")
    run()

"""Bounded local request client; uncertain mutations are never replayed."""

import json
import os
from pathlib import Path
import time
import uuid

ROOT = Path.home() / "Library/Application Support/FontLab8MCP"


def call(name, arguments=None, timeout=30):
    ready = json.loads((ROOT / "ready.json").read_text())
    try:
        os.kill(int(ready["pid"]), 0)
    except ProcessLookupError:
        raise RuntimeError(
            "FontLab 8 is not running; start it to load the installed native adapter"
        ) from None
    ident = uuid.uuid4().hex
    request = dict(
        name=name,
        arguments=arguments or {},
        session=ready["session"],
        expires=time.time() + timeout,
    )
    temporary = ROOT / "requests" / (ident + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(request, stream, allow_nan=False)
    temporary.rename(temporary.with_suffix(".json"))
    result = ROOT / "results" / (ident + ".json")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result.exists():
            data = json.loads(result.read_text())
            result.unlink()
            if data.get("session") != ready["session"]:
                raise RuntimeError(
                    "FontLab session changed while the request was outstanding; do not replay mutations"
                )
            if not data["ok"]:
                raise RuntimeError(data["error"] + "\n" + data.get("traceback", ""))
            return data["value"]
        time.sleep(0.05)
    raise TimeoutError(
        f"FontLab request {ident} timed out; execution outcome unknown. Do not replay a mutation."
    )

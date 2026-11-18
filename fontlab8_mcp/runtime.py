"""Main-thread file-queue transport inside FontLab 8; no worker touches font objects."""

import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback
import uuid
import types

ROOT = Path.home() / "Library/Application Support/FontLab8MCP"
SESSION = uuid.uuid4().hex
_timer = None
_busy = False
_last_output = ""
_python_namespace = None


def fontpr_module():
    from . import adapter

    module = types.ModuleType("fontpr")
    module.__doc__ = (
        "FontLab 8 compatibility facade for the ported FontLab 9 MCP subset."
    )
    for name in adapter.SUPPORTED - {"run_python"}:

        def invoke(_name=name, **arguments):
            return dispatch(_name, arguments)

        setattr(module, name, invoke)
    return module


def publish(path, data):
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    fd = os.open(str(temporary), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(data, stream, allow_nan=False)
    os.replace(str(temporary), str(path))


def dispatch(name, args):
    global _last_output, _python_namespace
    if name == "get_python_output":
        return dict(
            output="\n".join(
                _last_output.splitlines()[
                    -max(1, min(1000, int(args.get("lines", 100)))) :
                ]
            )
        )
    if name == "run_python":
        import fontlab, fontgate

        output = io.StringIO()
        if _python_namespace is None:
            _python_namespace = dict(fontlab=fontlab, fontgate=fontgate)
        namespace = _python_namespace
        module = fontpr_module()
        sys.modules["fontpr"] = module
        sys.modules["mcp_tools"] = module
        namespace.pop("result", None)
        try:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                exec(args["code"], namespace, namespace)
        finally:
            _last_output = output.getvalue()
        result = namespace.get("result")
        json.dumps(result, allow_nan=False)
        return dict(output=output.getvalue(), result=result)
    from . import adapter

    # Owned adapter handlers are stateless; refresh during this development port.
    importlib.reload(adapter)
    return adapter.dispatch(name, args)


def tick():
    global _busy
    if _busy:
        return
    _busy = True
    try:
        for path in sorted((ROOT / "requests").glob("*.json"))[:4]:
            claimed = path.with_suffix(".processing")
            try:
                path.rename(claimed)
                if claimed.stat().st_size > 2 * 1024 * 1024:
                    raise ValueError("Request exceeds 2 MiB")
                request = json.loads(claimed.read_text())
                if request.get("session") != SESSION:
                    raise ValueError("FontLab session changed; request not executed")
                if request.get("expires", 0) < time.time():
                    raise ValueError(
                        "Request expired before execution; no operation was performed"
                    )
                value = dispatch(request["name"], request.get("arguments", {}))
                response = dict(ok=True, value=value, session=SESSION)
            except Exception as exc:
                response = dict(
                    ok=False,
                    error=str(exc),
                    traceback=traceback.format_exc(),
                    session=SESSION,
                )
            publish(ROOT / "results" / path.name, response)
            claimed.unlink(missing_ok=True)
    finally:
        _busy = False


def start():
    global _timer
    if _timer is not None:
        return
    from PythonQt.QtCore import QTimer

    if "FontLab 8.app" not in sys.executable:
        raise RuntimeError(
            "This adapter must run inside FontLab 8, not another application"
        )

    for path in [ROOT, ROOT / "requests", ROOT / "results"]:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(str(path), 0o700)
    _timer = QTimer()
    _timer.timeout.connect(tick)
    _timer.start(100)
    publish(
        ROOT / "ready.json",
        dict(
            session=SESSION,
            pid=os.getpid(),
            python=sys.version,
            started=time.time(),
            product="FontLab 8",
        ),
    )
    print("FontLab 8 native MCP adapter ready")


def stop():
    global _timer
    if _timer is not None:
        _timer.stop()
        _timer = None
    ready = ROOT / "ready.json"
    if ready.exists() and json.loads(ready.read_text()).get("session") == SESSION:
        ready.unlink()

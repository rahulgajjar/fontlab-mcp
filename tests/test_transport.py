import json
import time
from fontlab8_mcp import runtime


def queue(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    (tmp_path / "requests").mkdir()
    (tmp_path / "results").mkdir()
    return tmp_path


def test_stale_sessions_and_expired_commands_cannot_edit(tmp_path, monkeypatch):
    root = queue(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(runtime, "dispatch", lambda *args: calls.append(args))
    for i, request in enumerate(
        [
            dict(session="old", expires=time.time() + 10),
            dict(session=runtime.SESSION, expires=time.time() - 1),
        ]
    ):
        request.update(
            name="set_font_info", arguments={"font_info": {"familyName": "wrong"}}
        )
        (root / "requests" / f"{i}.json").write_text(json.dumps(request))
    runtime.tick()
    assert calls == []
    results = [json.loads(p.read_text()) for p in (root / "results").glob("*.json")]
    assert len(results) == 2 and all(not r["ok"] for r in results)


def test_claimed_request_runs_once_and_error_does_not_block_next(tmp_path, monkeypatch):
    root = queue(tmp_path, monkeypatch)
    calls = []

    def dispatch(name, args):
        calls.append(name)
        if name == "bad":
            raise ValueError("invalid edit")
        return {"value": 42}

    monkeypatch.setattr(runtime, "dispatch", dispatch)
    for i, name in enumerate(["bad", "good"]):
        (root / "requests" / f"{i}.json").write_text(
            json.dumps(
                dict(session=runtime.SESSION, expires=time.time() + 10, name=name)
            )
        )
    runtime.tick()
    runtime.tick()
    assert calls == ["bad", "good"]
    assert json.loads((root / "results/1.json").read_text())["value"] == {"value": 42}

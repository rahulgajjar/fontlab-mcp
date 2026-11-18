from fontlab8_mcp import server

def rpc(method, params=None):
    return server.handle({"jsonrpc":"2.0", "id":1, "method":method, "params":params or {}})

def test_agent_discovery_and_guidance():
    init=rpc("initialize")["result"]
    assert "fgFont" in init["instructions"]
    assert "resources" in init["capabilities"] and "prompts" in init["capabilities"]
    uri=rpc("resources/list")["result"]["resources"][0]["uri"]
    text=rpc("resources/read", {"uri":uri})["result"]["contents"][0]["text"]
    assert "NOT transactional" in text and "fgFont.fg" in text
    name=rpc("prompts/list")["result"]["prompts"][0]["name"]
    assert rpc("prompts/get", {"name":name})["result"]["messages"][0]["content"]["text"] == text
    assert "error" in rpc("resources/read", {"uri":"invalid"})
    assert "error" in rpc("prompts/get", {"name":"invalid"})
    tools=rpc("tools/list")["result"]["tools"]
    assert "NOT transactional" in next(t for t in tools if t["name"]=="run_python")["description"]

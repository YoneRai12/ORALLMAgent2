from orallm.agent.tools import web_browse, file_ops


def test_web_browse_search(monkeypatch):
    def fake_get(url, params, timeout):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"AbstractText": "OpenAI creates AI"}

        return FakeResponse()

    monkeypatch.setattr(web_browse.requests, "get", fake_get)
    result = web_browse.search("openai")
    assert result == "OpenAI creates AI"


def test_file_ops_handle(tmp_path):
    file_path = tmp_path / "demo.txt"
    write_res = file_ops.handle("write", str(file_path), "hello")
    assert write_res == "write ok"
    append_res = file_ops.handle("append", str(file_path), " world")
    assert append_res == "append ok"
    read_res = file_ops.handle("read", str(file_path))
    assert read_res == "hello world"

from pathlib import Path

from orallm.agent import executor


def test_run_plan_executes_steps(tmp_path, monkeypatch):
    out_file = tmp_path / "out.txt"

    def fake_search(query: str) -> str:
        return "result for " + query

    monkeypatch.setitem(executor.TOOLS, "web_browse", fake_search)

    plan = [
        {"tool": "web_browse", "args": {"query": "python"}},
        {
            "tool": "file_ops",
            "args": {"action": "write", "path": str(out_file), "text": "data"},
        },
        {"tool": "file_ops", "args": {"action": "read", "path": str(out_file)}},
    ]

    results = executor.run_plan(plan)
    assert results[0] == "result for python"
    assert results[1] == "write ok"
    assert results[2] == "data"
    assert out_file.read_text() == "data"

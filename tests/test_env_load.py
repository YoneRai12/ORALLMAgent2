import os
from dotenv import load_dotenv

def test_load_dotenv_utf8(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("# 日本語コメント\nJWT_SECRET=testsecret\nRATE_LIMIT=10/minute\n", encoding="utf-8")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("RATE_LIMIT", raising=False)
    load_dotenv(dotenv_path=env_file, encoding="utf-8")
    assert os.getenv("JWT_SECRET") == "testsecret"
    assert os.getenv("RATE_LIMIT") == "10/minute"

"""Tests for inline Amazon credential handling."""

from __future__ import annotations

import pytest

from agent.parsers import parse_kv_pairs
from agent.security import SessionSecrets


def test_parse_kv_pairs() -> None:
    kv, sanitized = parse_kv_pairs('!amazon buy "Kindle" email=a@example.com pass=123')
    assert kv == {"email": "a@example.com", "pass": "123"}
    assert sanitized == "!amazon buy Kindle"


def test_session_secrets_zeroed() -> None:
    secrets = SessionSecrets("a@example.com", "123")
    with secrets as s:
        assert s.email == "a@example.com"
    with pytest.raises(AttributeError):
        repr(secrets.email)


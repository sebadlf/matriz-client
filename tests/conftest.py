from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from matriz_client import client as _client


@pytest.fixture
def reset_client_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset module-level auth state and inject dummy credentials."""
    monkeypatch.setattr(_client, "_token", "test-token")
    monkeypatch.setattr(_client, "_token_ts", time.time())
    monkeypatch.setattr(_client, "_user", "test-user")
    monkeypatch.setattr(_client, "_password", "test-pass")
    monkeypatch.setattr(_client, "_base_url", "https://api.test")


@pytest.fixture
def mock_session(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the requests session with a MagicMock."""
    mock = MagicMock()
    monkeypatch.setattr(_client, "_session", mock)
    return mock


def build_response(payload: dict[str, Any], headers: dict[str, str] | None = None) -> MagicMock:
    """Build a MagicMock response with json() and headers."""
    response = MagicMock()
    response.json.return_value = payload
    response.headers = headers or {}
    response.raise_for_status.return_value = None
    return response

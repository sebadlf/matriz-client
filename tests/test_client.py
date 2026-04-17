from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from matriz_client import client as _client
from matriz_client.exceptions import AuthenticationError, PrimaryAPIError
from tests.conftest import build_response

# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------


def test_login_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_client, "_user", "")
    monkeypatch.setattr(_client, "_password", "")
    monkeypatch.setattr(_client, "_token", None)
    with pytest.raises(AuthenticationError):
        _client.login()


def test_login_stores_token_from_header(
    monkeypatch: pytest.MonkeyPatch, mock_session: MagicMock
) -> None:
    monkeypatch.setattr(_client, "_user", "u")
    monkeypatch.setattr(_client, "_password", "p")
    monkeypatch.setattr(_client, "_token", None)
    monkeypatch.setattr(_client, "_token_ts", 0.0)
    mock_session.post.return_value = build_response({}, headers={"X-Auth-Token": "tkn-123"})

    token = _client.login()

    assert token == "tkn-123"
    assert _client._token == "tkn-123"
    assert _client._token_ts > 0


def test_login_raises_when_header_missing(
    monkeypatch: pytest.MonkeyPatch, mock_session: MagicMock
) -> None:
    monkeypatch.setattr(_client, "_user", "u")
    monkeypatch.setattr(_client, "_password", "p")
    monkeypatch.setattr(_client, "_token", None)
    mock_session.post.return_value = build_response({}, headers={})
    with pytest.raises(AuthenticationError):
        _client.login()


def test_ensure_token_skips_when_fresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_client, "_token", "fresh")
    monkeypatch.setattr(_client, "_token_ts", time.time())
    called = {"n": 0}

    def fake_login() -> str:
        called["n"] += 1
        return "new"

    monkeypatch.setattr(_client, "login", fake_login)
    _client._ensure_token()
    assert called["n"] == 0


def test_ensure_token_refreshes_when_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_client, "_token", "old")
    monkeypatch.setattr(_client, "_token_ts", time.time() - (24 * 60 * 60))
    called = {"n": 0}

    def fake_login() -> str:
        called["n"] += 1
        return "new"

    monkeypatch.setattr(_client, "login", fake_login)
    _client._ensure_token()
    assert called["n"] == 1


# ------------------------------------------------------------------
# Request plumbing
# ------------------------------------------------------------------


def test_request_raises_on_error_payload(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response(
        {"status": "ERROR", "description": "bad symbol", "message": "x"}
    )
    with pytest.raises(PrimaryAPIError) as exc:
        _client._request("GET", "/rest/anything")
    assert exc.value.description == "bad symbol"


def test_request_sends_auth_header(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response({"status": "OK"})
    _client._request("GET", "/rest/anything", params={"symbol": "DLR/DIC23"})
    _, kwargs = mock_session.request.call_args
    assert kwargs["headers"] == {"X-Auth-Token": "test-token"}
    assert kwargs["params"] == {"symbol": "DLR/DIC23"}


def test_request_with_basic_auth_skips_token(
    reset_client_state: None, mock_session: MagicMock
) -> None:
    mock_session.request.return_value = build_response({"status": "OK"})
    _client._request("GET", "/rest/risk/x", auth_basic=("u", "p"))
    _, kwargs = mock_session.request.call_args
    assert "headers" not in kwargs
    assert kwargs["auth"].username == "u"
    assert kwargs["auth"].password == "p"


def test_get_filters_none_params(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response({"status": "OK"})
    _client._get("/rest/x", symbol="ABC", foo=None, bar=1)
    _, kwargs = mock_session.request.call_args
    assert kwargs["params"] == {"symbol": "ABC", "bar": 1}


# ------------------------------------------------------------------
# Endpoint wrappers
# ------------------------------------------------------------------


def test_get_segments(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response(
        {"status": "OK", "segments": [{"marketSegmentId": "DDF"}]}
    )
    assert _client.get_segments() == [{"marketSegmentId": "DDF"}]
    args, _ = mock_session.request.call_args
    assert args[1].endswith("/rest/segment/all")


def test_get_instrument_detail_passes_symbol(
    reset_client_state: None, mock_session: MagicMock
) -> None:
    mock_session.request.return_value = build_response(
        {"status": "OK", "instrument": {"symbol": "DLR/DIC23"}}
    )
    result = _client.get_instrument_detail("DLR/DIC23")
    assert result == {"symbol": "DLR/DIC23"}
    _, kwargs = mock_session.request.call_args
    assert kwargs["params"] == {"symbol": "DLR/DIC23", "marketId": "ROFX"}


def test_new_order_builds_params(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response(
        {"status": "OK", "order": {"clientId": "abc", "proprietary": "PBCP"}}
    )
    _client.new_order(
        symbol="DLR/DIC23",
        side="BUY",
        qty=10,
        account="ACC1",
        price=123.5,
    )
    _, kwargs = mock_session.request.call_args
    params = kwargs["params"]
    assert params["symbol"] == "DLR/DIC23"
    assert params["side"] == "BUY"
    assert params["orderQty"] == 10
    assert params["account"] == "ACC1"
    assert params["price"] == 123.5
    assert params["ordType"] == "LIMIT"
    assert params["timeInForce"] == "DAY"
    assert params["cancelPrevious"] == "False"
    assert params["iceberg"] == "False"


def test_new_order_omits_optional_fields(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response({"status": "OK", "order": {}})
    _client.new_order(symbol="S", side="SELL", qty=1, account="A")
    _, kwargs = mock_session.request.call_args
    params = kwargs["params"]
    assert "price" not in params
    assert "displayQty" not in params
    assert "expireDate" not in params


def test_get_market_data_defaults(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response({"status": "OK", "marketData": {"LA": {}}})
    _client.get_market_data("DLR/DIC23")
    _, kwargs = mock_session.request.call_args
    assert kwargs["params"]["entries"] == "BI,OF,LA,OP,CL,SE,OI"
    assert kwargs["params"]["marketId"] == "ROFX"
    assert "depth" not in kwargs["params"]


def test_get_positions_uses_basic_auth(reset_client_state: None, mock_session: MagicMock) -> None:
    mock_session.request.return_value = build_response({"status": "OK", "positions": []})
    _client.get_positions("ACC1")
    args, kwargs = mock_session.request.call_args
    assert args[1].endswith("/rest/risk/position/getPositions/ACC1")
    assert "headers" not in kwargs
    assert kwargs["auth"] is not None

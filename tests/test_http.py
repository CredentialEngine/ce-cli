from types import SimpleNamespace
from unittest.mock import Mock

import httpx2
import pytest

from ce.utils import http

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_http_methods(monkeypatch, method):
    transport = Mock()
    transport.request.return_value = httpx2.Response(200, json={"ok": True})
    factory = Mock(return_value=transport)
    monkeypatch.setattr(http.httpx2, "Client", factory)
    with http.CEHTTPClient("https://api.example", "fixture") as client:
        assert getattr(client, method)("/example").json() == {"ok": True}
    transport.request.assert_called_once_with(method.upper(), "/example")
    transport.close.assert_called_once()
    assert factory.call_args.kwargs["headers"]["User-Agent"] == http.USER_AGENT


@pytest.mark.parametrize(
    "body,expected",
    [
        ({"message": "message"}, "message"),
        ({"error_description": "description"}, "description"),
        ({"error": "error"}, "error"),
        (["invalid"], '["invalid"]'),
    ],
)
def test_http_error_json(body, expected):
    with pytest.raises(http.APIError) as exc:
        http.CEHTTPClient._raise_for_status(httpx2.Response(400, json=body))
    assert exc.value.status_code == 400
    assert exc.value.message == expected


def test_http_error_empty():
    with pytest.raises(http.APIError, match="HTTP 500"):
        http.CEHTTPClient._raise_for_status(httpx2.Response(500))


def test_authenticated_context_closes_on_exception(monkeypatch):
    transport = Mock()
    monkeypatch.setattr(http.httpx2, "Client", Mock(return_value=transport))
    monkeypatch.setattr(http, "require_login", lambda: "fixture")
    monkeypatch.setattr(
        "ce.config.context.require_environment",
        lambda: ("sandbox", SimpleNamespace(publisher_base="https://api.example/")),
    )
    with pytest.raises(RuntimeError, match="example"), http.api_client(timeout=7):
        raise RuntimeError("example")
    transport.close.assert_called_once()

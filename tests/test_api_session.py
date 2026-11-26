"""Saved login and per-request authentication for the API command groups."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import click
import httpx2
import pytest
from consumer_api_client.exceptions import ApiException

from ce.auth import api_session
from ce.auth.token_manager import NOT_LOGGED_IN, TokenResult
from ce.implementations.publisher.client import PublisherClient
from ce.registry import api as consumer_api


def test_missing_login(monkeypatch):
    monkeypatch.setattr(
        api_session,
        "resolve_access_token",
        Mock(return_value=TokenResult(reason=NOT_LOGGED_IN)),
    )
    with pytest.raises(click.ClickException, match="ce login"):
        api_session.require_api_token("dev")


def test_publisher_refreshes_only_rejected_request():
    seen = []

    def handler(request):
        seen.append(request.headers["Authorization"])
        return httpx2.Response(401 if len(seen) == 1 else 200, json=[])

    with PublisherClient(
        "https://publisher.example", "old", transport=httpx2.MockTransport(handler)
    ) as client:
        client.token_provider = lambda *, force_refresh=False: (
            "new" if force_refresh else "old"
        )
        assert client.list_projects() == []
    assert seen == ["Bearer old", "Bearer new"]


def test_registry_retries_only_one_sdk_call(monkeypatch):
    config = SimpleNamespace(access_token=None)
    seen = []

    async def request():
        seen.append(config.access_token)
        if len(seen) == 1:
            raise ApiException(status=401)
        return "ok"

    monkeypatch.setattr(
        consumer_api,
        "require_api_token",
        lambda env, *, force_refresh=False: "new" if force_refresh else "old",
    )
    api = consumer_api.AuthenticatedApi(SimpleNamespace(request=request), config, "dev")
    assert asyncio.run(api.request()) == "ok"
    assert seen == ["old", "new"]


@pytest.mark.parametrize("status", [401, 403])
def test_registry_stops_on_rejection(monkeypatch, status):
    provider = Mock(return_value="token")
    monkeypatch.setattr(consumer_api, "require_api_token", provider)
    method = AsyncMock(side_effect=ApiException(status=status))
    api = consumer_api.AuthenticatedApi(
        SimpleNamespace(request=method), SimpleNamespace(), "dev"
    )
    error = click.ClickException if status == 401 else ApiException
    with pytest.raises(error):
        asyncio.run(api.request())
    assert method.await_count == (2 if status == 401 else 1)

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import click
import httpx2
import pytest

from ce.registry import resources

GUID = "12345678-1234-1234-1234-123456789abc"


CTID = "ce-" + GUID


@pytest.mark.parametrize(
    "identifier,expected",
    [
        (CTID, ("ctid", CTID)),
        (GUID, ("bnode", UUID(GUID))),
        ("_:" + GUID, ("bnode", UUID(GUID))),
    ],
)
def test_identifier(identifier, expected):
    assert resources.parse_identifier(identifier) == expected


@pytest.mark.parametrize("kind", ["graphs", "metadata"])
def test_unsupported_bnode(kind):
    with pytest.raises(click.UsageError, match="CTID only"):
        resources.execute_lookup(None, kind, GUID)


@pytest.fixture
def registry_sdk(monkeypatch):
    api = SimpleNamespace()
    client = AsyncMock()
    client.__aenter__.return_value = client
    monkeypatch.setattr(resources, "ApiClient", Mock(return_value=client))
    monkeypatch.setattr(
        resources,
        "require_environment",
        lambda: (
            "sandbox",
            SimpleNamespace(consumer_api_base="https://api.example", ssl_verify=True),
        ),
    )
    monkeypatch.setattr(resources, "require_api_token", Mock(return_value="fixture"))
    monkeypatch.setattr(
        "ce.registry.api.require_api_token", Mock(return_value="fixture")
    )
    monkeypatch.setattr(resources, "ResourceApi", Mock(return_value=api))
    return api, client


@pytest.mark.parametrize(
    "response,match",
    [
        (httpx2.Response(404), "HTTP 404"),
        (httpx2.Response(200, content=b"not json"), "invalid JSON"),
    ],
)
def test_lookup_failure(registry_sdk, response, match):
    api, _ = registry_sdk
    api.resource_get_resource_by_ctid_without_preload_content = AsyncMock(
        return_value=response
    )
    with pytest.raises(click.ClickException, match=match):
        resources.execute_lookup(None, "resources", CTID)
    assert response.is_closed

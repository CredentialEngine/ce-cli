from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import click
import httpx2
import pytest
from click.testing import CliRunner

from ce.commands.registry import registry_group
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


@pytest.mark.parametrize(
    "kind,identifier,api_class,method,expected",
    [
        (
            "resources",
            CTID,
            "ResourceApi",
            "resource_get_resource_by_ctid_without_preload_content",
            CTID,
        ),
        (
            "resources",
            "_:" + GUID,
            "ResourceApi",
            "resource_get_resource_by_bnode_guid_without_preload_content",
            UUID(GUID),
        ),
        (
            "graphs",
            CTID,
            "GraphApi",
            "graph_get_graph_by_ctid_without_preload_content",
            CTID,
        ),
        (
            "metadata",
            CTID,
            "MetadataApi",
            "metadata_get_metadata_by_ctid_without_preload_content",
            CTID,
        ),
    ],
)
def test_lookup(monkeypatch, kind, identifier, api_class, method, expected):
    call = AsyncMock(return_value=httpx2.Response(200, json={"example": True}))

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            assert self.user_agent == resources.USER_AGENT

    monkeypatch.setattr(resources, "ApiClient", lambda config: Client())
    monkeypatch.setattr(
        resources, api_class, lambda client: SimpleNamespace(**{method: call})
    )
    monkeypatch.setattr(
        resources,
        "require_environment",
        lambda: (
            "dev",
            SimpleNamespace(consumer_api_base="https://api.example", ssl_verify=True),
        ),
    )
    monkeypatch.setattr(resources, "require_api_token", lambda *a, **kw: "token")
    monkeypatch.setattr("ce.registry.api.require_api_token", lambda *a, **kw: "token")
    result = CliRunner().invoke(registry_group, [kind, "get", identifier])
    assert result.exit_code == 0, result.exception
    assert call.await_args.args == (expected,)
    assert '"example": true' in result.output

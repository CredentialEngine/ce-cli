"""Point lookups using the existing Consumer API SDK operations."""

import asyncio
import json
from urllib.parse import urlsplit
from uuid import UUID

import click
import httpx2
from consumer_api_client import ApiClient, Configuration
from consumer_api_client.api.graph_api import GraphApi
from consumer_api_client.api.metadata_api import MetadataApi
from consumer_api_client.api.resource_api import ResourceApi
from consumer_api_client.exceptions import ApiException

from ce.auth.api_session import require_api_token
from ce.config.context import require_environment
from ce.registry.api import AuthenticatedApi
from ce.utils.user_agent import USER_AGENT


def parse_identifier(identifier):
    """Return a CTID or a UUID, stripping the JSON-LD blank-node prefix."""
    ctid = identifier.lower().startswith("ce-")
    try:
        guid = UUID(identifier[3:] if ctid else identifier.removeprefix("_:"))
    except ValueError:
        raise click.BadParameter(
            "Expected a ce- CTID or a blank-node GUID.", param_hint="identifier"
        ) from None
    return ("ctid", f"ce-{guid}") if ctid else ("bnode", guid)


def execute_lookup(ctx, kind, identifier, depth=None):
    id_kind, value = parse_identifier(identifier)
    if kind != "resources" and id_kind != "ctid":
        raise click.UsageError(
            f"The installed Consumer API SDK supports {kind} lookup by CTID only."
        )
    env_name, env = require_environment()
    base = (env.consumer_api_base or "").rstrip("/")
    origin = urlsplit(base)
    if (
        origin.scheme not in {"http", "https"}
        or not origin.hostname
        or origin.username
        or origin.password
        or origin.query
        or origin.fragment
    ):
        raise click.UsageError("Consumer API base URL is not configured correctly.")
    token = require_api_token(env_name)

    async def run():
        config = Configuration(host=base, access_token=token, verify_ssl=env.ssl_verify)
        async with ApiClient(config) as client:
            client.user_agent = USER_AGENT
            if kind == "resources":
                api = AuthenticatedApi(ResourceApi(client), config, env_name)
                method = (
                    api.resource_get_resource_by_ctid_without_preload_content
                    if id_kind == "ctid"
                    else api.resource_get_resource_by_bnode_guid_without_preload_content
                )
                response = await method(value, _request_timeout=60.0)
            elif kind == "graphs":
                api = AuthenticatedApi(GraphApi(client), config, env_name)
                response = await api.graph_get_graph_by_ctid_without_preload_content(
                    value, depth=depth, _request_timeout=60.0
                )
            else:
                api = AuthenticatedApi(MetadataApi(client), config, env_name)
                response = (
                    await api.metadata_get_metadata_by_ctid_without_preload_content(
                        value, _request_timeout=60.0
                    )
                )
            try:
                if response.status_code != 200:
                    raise click.ClickException(
                        f"Consumer API request failed (HTTP {response.status_code})."
                    )
                await response.aread()
                click.echo(json.dumps(response.json(), indent=2, ensure_ascii=False))
            finally:
                await response.aclose()

    try:
        asyncio.run(run())
    except ApiException as exc:
        raise click.ClickException(
            f"Consumer API request failed (HTTP {exc.status})."
        ) from None
    except httpx2.HTTPError:
        raise click.ClickException("Could not reach Consumer API.") from None
    except ValueError:
        raise click.ClickException(
            "Consumer API returned an invalid JSON response."
        ) from None

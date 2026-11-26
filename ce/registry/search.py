"""Registry search and asynchronous export creation using the Consumer API SDK."""

from __future__ import annotations

import asyncio
import csv
import io
import json
import re
from urllib.parse import urlencode, urlsplit

import click
import httpx2
from consumer_api_client import ApiClient, Configuration
from consumer_api_client.api.export_api import ExportApi
from consumer_api_client.exceptions import ApiException
from consumer_api_client.models.create_search_export_request import (
    CreateSearchExportRequest,
)

from ce.auth.api_session import require_api_token
from ce.config.context import require_environment
from ce.registry.api import AuthenticatedApi
from ce.utils.display import new_console, plain_table
from ce.utils.user_agent import USER_AGENT

_INDEXED_FILTER = re.compile(
    r"--filters?\[(0|[1-9][0-9]*)\]\.(field|operator|value|values)(?:\[(0|[1-9][0-9]*)\])?"
)


def normalize_filter_args(args):
    """Translate indexed CLI options into the existing JSON filter input."""
    result = []
    filters = {}
    indexed_values = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            result.extend(args[i:])
            break
        name, separator, value = arg.partition("=")
        match = _INDEXED_FILTER.fullmatch(name)
        if not match:
            if name.startswith(("--filter[", "--filters[")):
                raise click.UsageError(f"Invalid filter option: {name}")
            result.append(arg)
            # Do not interpret the value of an ordinary search option as a flag.
            if (
                not separator
                and name
                in {
                    "--query",
                    "--type",
                    "--language",
                    "--index-type",
                    "--index-id",
                    "--page",
                    "--view",
                    "--filters",
                    "--output",
                    "-o",
                }
                and i + 1 < len(args)
            ):
                i += 1
                result.append(args[i])
            i += 1
            continue
        index, field, value_index = match.groups()
        if value_index is not None and field != "values":
            raise click.UsageError(f"Only values may have an array index: {name}")
        if not separator:
            i += 1
            if i == len(args) or args[i].startswith("--"):
                raise click.UsageError(f"Missing value for {name}")
            value = args[i]
        item = filters.setdefault(int(index), {})
        if field == "values" and value_index is not None:
            if field in item:
                raise click.UsageError(
                    "Do not mix indexed and repeated values for a filter."
                )
            values = indexed_values.setdefault(int(index), {})
            if int(value_index) in values:
                raise click.UsageError(f"Duplicate filter option: {name}")
            values[int(value_index)] = value
        elif field == "values":
            if int(index) in indexed_values:
                raise click.UsageError(
                    "Do not mix indexed and repeated values for a filter."
                )
            item.setdefault(field, []).append(value)
        else:
            if field in item:
                raise click.UsageError(f"Duplicate filter option: {name}")
            item[field] = value
        i += 1
    if filters:
        if sorted(filters) != list(range(len(filters))):
            raise click.UsageError("Filter indexes must start at 0 and be consecutive.")
        for index, values in indexed_values.items():
            if sorted(values) != list(range(len(values))):
                raise click.UsageError(
                    "Filter value indexes must start at 0 and be consecutive."
                )
            filters[index]["values"] = [values[j] for j in sorted(values)]
        result = [
            "--filters",
            json.dumps([filters[j] for j in sorted(filters)]),
        ] + result
    return result


class IndexedFilterCommand(click.Command):
    def parse_args(self, ctx, args):
        return super().parse_args(ctx, normalize_filter_args(args))


class IndexedFilterGroup(click.Group):
    def parse_args(self, ctx, args):
        # The export subcommand parses its own options.
        if args and args[0] == "export":
            return super().parse_args(ctx, args)
        return super().parse_args(ctx, normalize_filter_args(args))


def search_options(fn):
    options = [
        click.option("--query", help="Search text or CTID."),
        click.option("--type", "resource_type", help="CTDL resource type."),
        click.option("--language", help="Preferred resource language."),
        click.option(
            "--include-bnodes/--no-include-bnodes", default=True, show_default=True
        ),
        click.option("--index-type", help="Search index type, e.g. es."),
        click.option("--index-id", help="Search index identifier."),
        click.option("--page", type=click.IntRange(min=0)),
        click.option(
            "--view",
            type=click.Choice(
                ["Summary", "Detail", "JsonLd", "Ids", "Suggestion"],
                case_sensitive=False,
            ),
        ),
        click.option(
            "--filters",
            multiple=True,
            help="JSON filter object or array; repeatable. Alternatively use --filter[0].field, --filter[0].operator, --filter[0].value or --filter[0].values (repeatable).",
        ),
    ]
    for option in reversed(options):
        fn = option(fn)
    return fn


_SCHEMA_TERM = re.compile(
    r"(?:[A-Za-z][A-Za-z0-9_-]*:[A-Za-z][A-Za-z0-9_-]*|https?://[^\s]+)"
)


def require_schema_term(value, option, *, keywords=()):
    if value not in keywords and not _SCHEMA_TERM.fullmatch(value):
        raise click.BadParameter(
            "Use a CTDL schema term (e.g. ceterms:Credential or ceterms:ownedBy), not a display label.",
            param_hint=option,
        )


def build_search_url(
    base,
    *,
    query=None,
    resource_type=None,
    language=None,
    include_bnodes=True,
    index_type=None,
    index_id=None,
    page=None,
    view=None,
    filters=(),
):
    if resource_type is not None:
        require_schema_term(resource_type, "--type")
    params = [
        (k, v)
        for k, v in [
            ("query", query),
            ("type", resource_type),
            ("language", language),
            ("includeBnodes", str(include_bnodes).lower()),
            ("indexType", index_type),
            ("indexId", index_id),
            ("page", page),
            ("view", view),
        ]
        if v is not None
    ]
    parsed = []
    for raw in filters:
        try:
            value = json.loads(raw)
        except ValueError:
            raise click.BadParameter(
                "Expected a JSON filter object or array.", param_hint="--filters"
            ) from None
        parsed.extend(value if isinstance(value, list) else [value])
    if not (query and query.strip()) and not parsed:
        raise click.UsageError("Specify --query or --filters.")
    for i, item in enumerate(parsed):
        if not isinstance(item, dict) or not set(item) <= {
            "field",
            "operator",
            "value",
            "values",
        }:
            raise click.BadParameter("Invalid filter object.", param_hint="--filters")
        field, op = item.get("field"), item.get("operator")
        if (
            not isinstance(field, str)
            or not field.strip()
            or not isinstance(op, str)
            or op.upper()
            not in {
                "MATCHES",
                "EQUALS",
                "HAS_FIELD",
                "CONTAINS",
                "IN",
                "UNDER",
                "STARTS_WITH",
            }
        ):
            raise click.BadParameter(
                "Filter requires a field and supported operator.",
                param_hint="--filters",
            )
        require_schema_term(field, "--filters", keywords=("@id", "@type"))
        op = op.upper()
        value, values = item.get("value"), item.get("values")
        scalar = isinstance(value, str) and bool(value.strip())
        multiple = (
            isinstance(values, list)
            and bool(values)
            and all(isinstance(v, str) and v.strip() for v in values)
        )
        if not (
            (op == "HAS_FIELD" and value is None and values is None)
            or (op in {"IN", "UNDER"} and multiple and value is None)
            or (op not in {"HAS_FIELD", "IN", "UNDER"} and scalar and values is None)
        ):
            raise click.BadParameter(
                "Filter value(s) do not match its operator.", param_hint="--filters"
            )
        if field == "@type":
            for term in [value] if scalar else values if multiple else []:
                require_schema_term(term, "--filters")
        params.extend([(f"filters[{i}].field", field), (f"filters[{i}].operator", op)])
        if scalar:
            params.append((f"filters[{i}].value", value))
        if multiple:
            params.extend((f"filters[{i}].values", v) for v in values)
    return base.rstrip("/") + "/search?" + urlencode(params)


def _display_value(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "; ".join(filter(None, map(_display_value, value)))
    if isinstance(value, dict):
        for key in ("@value", "en-US", "en", "en-us"):
            if key in value:
                return _display_value(value[key])
        return next(
            (text for item in value.values() if (text := _display_value(item))), ""
        )
    return ""


def project_search_json(payload):
    """Return only the API total and projected search results."""
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise click.ClickException("Unexpected search response.")

    def project(result):
        if not isinstance(result, dict):
            return {
                "@id": result if isinstance(result, str) else None,
                "ceterms:ctid": None,
                "ceterms:name": None,
                "ceterms:description": None,
                "@type": None,
            }
        row = result.get("properties", result)
        if not isinstance(row, dict):
            row = result

        def field(*keys):
            for source in (row, result):
                for key in keys:
                    if source.get(key) is not None:
                        return source[key]
            return None

        return {
            "@id": field("@id", "id"),
            "ceterms:ctid": field("ceterms:ctid", "ctid"),
            "ceterms:name": field(
                "ceterms:name",
                "name",
                "ceasn:name",
                "ceasn:competencyText",
                "skos:prefLabel",
            ),
            "ceterms:description": field(
                "ceterms:description",
                "description",
                "ceasn:description",
                "skos:definition",
            ),
            "@type": field("@type", "types", "type"),
        }

    return {
        "total": _search_total(payload),
        "results": [project(result) for result in payload["results"]],
    }


def _search_total(payload):
    total = payload.get("total")
    return total.get("value") if isinstance(total, dict) else total


def _print_search_total(payload, *, err=False):
    total = _search_total(payload)
    click.echo(f"Total results: {total if total is not None else 'Unknown'}", err=err)


_SEARCH_COLUMNS = (
    "@id",
    "ceterms:ctid",
    "ceterms:name",
    "ceterms:description",
    "@type",
)


def print_search_tsv(payload):
    rows = project_search_json(payload)["results"]
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(_SEARCH_COLUMNS)
    for row in rows:
        writer.writerow(
            [
                ""
                if row[key] is None
                else row[key]
                if isinstance(row[key], str)
                else json.dumps(row[key], ensure_ascii=False, separators=(",", ":"))
                for key in _SEARCH_COLUMNS
            ]
        )
    click.echo(buffer.getvalue(), nl=False)
    _print_search_total(payload, err=True)


def print_search_results(payload):
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        raise click.ClickException("Unexpected search response.")
    if not results:
        _print_search_total(payload)
        return
    table = plain_table(["CTID", "Title", "Description"])
    for result in results:
        if not isinstance(result, dict):
            table.add_row(_display_value(result), "", "")
            continue
        row = result.get("properties", result)
        if not isinstance(row, dict):
            row = result

        def field(*keys, row=row):
            return next(
                (text for key in keys if (text := _display_value(row.get(key)))), ""
            )

        table.add_row(
            field("ctid", "ceterms:ctid", "id", "@id"),
            field("name", "title", "ceterms:name", "ceasn:name", "skos:prefLabel"),
            field(
                "description",
                "ceterms:description",
                "ceasn:description",
                "skos:definition",
            ),
        )
    new_console().print(table)
    _print_search_total(payload)


class SearchTransport:
    """Use SDK transport to preserve ASP.NET indexed query keys and raw views."""

    def __init__(self, client, config):
        self.client, self.config = client, config

    async def get(self, url):
        result = await self.client.rest_client.request(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {self.config.access_token}",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            _request_timeout=60.0,
        )
        return result.response


def execute_search(ctx, *, export=False, output_fmt="table", **params):
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
    if export and origin.scheme != "https":
        raise click.UsageError("Search exports require an HTTPS Consumer API URL.")
    url = build_search_url(base, **params)
    token = require_api_token(env_name)

    async def run():
        config = Configuration(host=base, access_token=token, verify_ssl=env.ssl_verify)
        async with ApiClient(config) as client:
            client.user_agent = USER_AGENT
            if export:
                api = AuthenticatedApi(ExportApi(client), config, env_name)
                response = (
                    await api.export_create_search_export_without_preload_content(
                        CreateSearchExportRequest(url=url), _request_timeout=60.0
                    )
                )
            else:
                api = AuthenticatedApi(
                    SearchTransport(client, config), config, env_name
                )
                response = await api.get(url)
            try:
                if response.status_code != (202 if export else 200):
                    raise click.ClickException(
                        f"Consumer API request failed (HTTP {response.status_code})."
                    )
                await response.aread()
                payload = response.json()
                if export:
                    job_id = payload.get("id") if isinstance(payload, dict) else None
                    if not job_id:
                        raise click.ClickException(
                            "Export accepted but response did not contain a job ID."
                        )
                    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
                    click.echo(
                        f"Track with: ce registry downloads search show {job_id}",
                        err=True,
                    )
                elif output_fmt == "json":
                    click.echo(
                        json.dumps(
                            project_search_json(payload), indent=2, ensure_ascii=False
                        )
                    )
                elif output_fmt == "tsv":
                    print_search_tsv(payload)
                else:
                    print_search_results(payload)
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


@click.group("search", cls=IndexedFilterGroup, invoke_without_command=True)
@search_options
@click.option(
    "-o",
    "--output",
    "output_fmt",
    type=click.Choice(["table", "json", "tsv"], case_sensitive=False),
    default="table",
    show_default=True,
)
@click.pass_context
def search_group(ctx, **params):
    """Search Registry resources or create an asynchronous search export."""
    if ctx.invoked_subcommand is None:
        if (
            ctx.get_parameter_source("output_fmt")
            != click.core.ParameterSource.COMMANDLINE
        ):
            params.pop("output_fmt", None)
        execute_search(ctx, **params)
    elif any(
        ctx.get_parameter_source(k) == click.core.ParameterSource.COMMANDLINE
        for k in params
    ):
        raise click.UsageError(
            "For an export, specify search options after the export command."
        )


@search_group.command("export", cls=IndexedFilterCommand)
@search_options
@click.pass_context
def export_search(ctx, **params):
    """Create a search export job and return its ID."""
    execute_search(ctx, export=True, **params)

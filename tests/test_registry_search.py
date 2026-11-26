from urllib.parse import parse_qs, urlsplit

import click
import pytest
from click.testing import CliRunner

from ce.registry import search


def test_search_options(monkeypatch):
    calls = []
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    runner = CliRunner()
    opts = ["--query", "nursing", "--type", "ceterms:Credential", "--no-include-bnodes"]
    assert runner.invoke(search.search_group, opts).exit_code == 0
    assert runner.invoke(search.search_group, ["export", *opts]).exit_code == 0
    assert calls[1].pop("export") is True
    assert calls[0] == calls[1]


def test_filter_encoding():
    url = search.build_search_url(
        "https://api.example",
        filters=['{"field":"ceterms:ownedBy","operator":"IN","values":["a","b"]}'],
    )
    query = parse_qs(urlsplit(url).query)
    assert query["filters[0].values"] == ["a", "b"]
    assert query["includeBnodes"] == ["true"]


def test_requires_query_or_filters():
    with pytest.raises(click.UsageError):
        search.build_search_url("https://api.example")


@pytest.mark.parametrize(
    "export,output_fmt", [(False, "table"), (False, "json"), (True, "table")]
)
def test_sdk_request_and_job_id(monkeypatch, capsys, export, output_fmt):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    import httpx2

    base = "https://api.example"
    monkeypatch.setenv("CE_REGISTRY_API_URL", "https://untrusted.example")
    monkeypatch.setenv("CE_CONSUMER_API_URL", "https://untrusted.example")
    payload = (
        {"id": "job123", "status": "Accepted"}
        if export
        else {
            "results": (
                [
                    {
                        "id": "urn:test",
                        "ctid": "ce-example",
                        "name": "Nursing",
                        "description": "A credential",
                        "types": ["ceterms:Credential"],
                        "ownedBy": "ignored",
                    }
                ]
                if output_fmt == "json"
                else []
            ),
            "total": {"value": 1 if output_fmt == "json" else 0},
        }
    )
    response = httpx2.Response(202 if export else 200, json=payload)
    rest = AsyncMock(return_value=SimpleNamespace(response=response))
    create = AsyncMock(return_value=response)

    class Client:
        def __init__(self, config):
            assert config.host == base
            self.rest_client = SimpleNamespace(request=rest)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(
        search,
        "require_environment",
        lambda: ("dev", SimpleNamespace(consumer_api_base=base, ssl_verify=True)),
    )
    monkeypatch.setattr(search, "require_api_token", lambda *a, **kw: "saved-token")
    monkeypatch.setattr(
        "ce.registry.api.require_api_token", lambda *a, **kw: "saved-token"
    )
    monkeypatch.setattr(search, "ApiClient", Client)
    monkeypatch.setattr(
        search,
        "ExportApi",
        lambda client: SimpleNamespace(
            export_create_search_export_without_preload_content=create
        ),
    )
    search.execute_search(
        SimpleNamespace(
            obj={
                "registry_url": "https://untrusted.example",
                "consumer_url": "https://untrusted.example",
            }
        ),
        export=export,
        query="nursing",
        output_fmt=output_fmt,
    )
    captured = capsys.readouterr()
    if export:
        assert create.await_args.args[0].url.startswith(base + "/search?")
        assert "job123" in captured.out
        assert "ce registry downloads search show job123" in captured.err
        assert not rest.called
    else:
        assert rest.await_args.args[0] == "GET"
        assert (
            rest.await_args.kwargs["headers"]["Authorization"] == "Bearer saved-token"
        )
        assert rest.await_args.kwargs["headers"]["User-Agent"] == search.USER_AGENT
        if output_fmt == "json":
            import json

            assert json.loads(captured.out) == {
                "results": [
                    {
                        "@id": "urn:test",
                        "ceterms:ctid": "ce-example",
                        "ceterms:name": "Nursing",
                        "ceterms:description": "A credential",
                        "@type": ["ceterms:Credential"],
                    }
                ],
                "total": 1,
            }
        else:
            assert captured.out.strip() == "Total results: 0"
        assert not create.called


def test_registry_search_independent_of_download_modules(monkeypatch):
    import builtins

    from ce.commands.registry import registry_group

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in {"ce.registry.downloads", "ce.utils.download_progress"}:
            raise AssertionError(f"Search imported download implementation: {name}")
        return original_import(name, *args, **kwargs)

    calls = []
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    runner = CliRunner()
    for args in (
        ["search", "--query", "nursing"],
        ["search", "export", "--query", "nursing"],
    ):
        result = runner.invoke(registry_group, args)
        assert result.exit_code == 0, result.exception
    assert len(calls) == 2
    assert calls[1]["export"] is True


@pytest.mark.parametrize("prefix", [[], ["export"]])
def test_indexed_filters(monkeypatch, prefix):
    calls = []
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    result = CliRunner().invoke(
        search.search_group,
        prefix
        + [
            "--filter[1].field",
            "ceterms:ownedBy",
            "--filter[1].operator=IN",
            "--filter[1].values[1]",
            "b",
            "--filter[1].values[0]",
            "a",
            "--filter[0].field",
            "ceterms:name",
            "--filter[0].operator",
            "MATCHES",
            "--filter[0].value",
            "nursing",
        ],
    )
    assert result.exit_code == 0, result.output
    params = calls[0]
    assert params.pop("export", False) == bool(prefix)
    query = parse_qs(
        urlsplit(search.build_search_url("https://api.example", **params)).query
    )
    assert query["filters[0].value"] == ["nursing"]
    assert query["filters[1].values"] == ["a", "b"]


@pytest.mark.parametrize(
    "args",
    [
        ["--filter[1].field", "name"],
        ["--filter[0].unknown", "name"],
        ["--filter[0].field"],
        ["--filter[0].field", "name", "--filter[0].field", "other"],
        ["--filter[0].values[1]", "a"],
    ],
)
def test_invalid_indexed_filters(args):
    result = CliRunner().invoke(search.search_group, args)
    assert result.exit_code == 2
    assert "Error:" in result.output


def test_repeated_filter_values():
    args = search.normalize_filter_args(
        [
            "--filter[0].field",
            "ceterms:name",
            "--filter[0].operator",
            "IN",
            "--filter[0].values",
            "a",
            "--filter[0].values",
            "b",
        ]
    )
    query = parse_qs(
        urlsplit(
            search.build_search_url("https://api.example", filters=[args[1]])
        ).query
    )
    assert query["filters[0].values"] == ["a", "b"]


@pytest.mark.parametrize("option", ["-o", "--output"])
def test_json_output_option(monkeypatch, option):
    calls = []
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    result = CliRunner().invoke(
        search.search_group, ["--query", "nursing", option, "json"]
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["output_fmt"] == "json"


def test_summary_table(capsys):
    search.print_search_results(
        {
            "results": [
                {
                    "ctid": "ce-example",
                    "name": "Nursing",
                    "description": "A credential",
                    "types": ["internal"],
                }
            ]
        }
    )
    text = capsys.readouterr().out
    for value in [
        "CTID",
        "Title",
        "Description",
        "ce-example",
        "Nursing",
        "A credential",
    ]:
        assert value in text
    assert "internal" not in text


def test_jsonld_table(capsys):
    search.print_search_results(
        {
            "results": [
                {
                    "properties": {
                        "ceterms:ctid": "ce-example",
                        "ceasn:name": {"en": "Nursing"},
                        "ceasn:description": {"en": ["A credential"]},
                    }
                }
            ]
        }
    )
    text = capsys.readouterr().out
    assert "Nursing" in text and "A credential" in text


@pytest.mark.parametrize("wrapped", [False, True])
def test_json_projection_preserves_real_types_and_values(wrapped):
    resource = {
        "@id": "urn:test",
        "ceterms:ctid": "ce-example",
        "ceasn:name": {"en": "Competency"},
        "ceasn:description": {"en": ["Description"]},
        "@type": ["ceasn:Competency", "https://example.org/OtherType"],
        "other": "excluded",
    }
    payload = {
        "results": [{"properties": resource} if wrapped else resource],
        "total": {"value": 1},
    }
    assert search.project_search_json(payload) == {
        "results": [
            {
                "@id": "urn:test",
                "ceterms:ctid": "ce-example",
                "ceterms:name": {"en": "Competency"},
                "ceterms:description": {"en": ["Description"]},
                "@type": ["ceasn:Competency", "https://example.org/OtherType"],
            }
        ],
        "total": 1,
    }


def test_json_projection_missing_fields_are_not_invented():
    assert search.project_search_json({"results": [{"id": "urn:test"}]})["results"] == [
        {
            "@id": "urn:test",
            "ceterms:ctid": None,
            "ceterms:name": None,
            "ceterms:description": None,
            "@type": None,
        }
    ]


def test_tsv_schema_headers_and_values(capsys):
    import csv
    import io
    import json

    search.print_search_tsv(
        {
            "results": [
                {
                    "id": "urn:test",
                    "ctid": "ce-example",
                    "name": "A\tB",
                    "description": "Line 1\nLine 2",
                    "types": ["ceterms:Credential"],
                }
            ]
        }
    )
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert rows[0] == [
        "@id",
        "ceterms:ctid",
        "ceterms:name",
        "ceterms:description",
        "@type",
    ]
    assert rows[1][:4] == ["urn:test", "ce-example", "A\tB", "Line 1\nLine 2"]
    assert json.loads(rows[1][4]) == ["ceterms:Credential"]


def test_empty_tsv_has_headers(capsys):
    search.print_search_tsv({"results": []})
    assert (
        capsys.readouterr().out
        == "@id\tceterms:ctid\tceterms:name\tceterms:description\t@type\n"
    )


@pytest.mark.parametrize(
    "params",
    [
        {"query": "nursing", "resource_type": "Credential"},
        {"filters": ['{"field":"name","operator":"MATCHES","value":"nursing"}']},
        {"filters": ['{"field":"@type","operator":"EQUALS","value":"Credential"}']},
    ],
)
def test_reject_unqualified_schema_terms(params):
    with pytest.raises(click.BadParameter):
        search.build_search_url("https://api.example", **params)


def test_tsv_option(monkeypatch):
    calls = []
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    result = CliRunner().invoke(
        search.search_group, ["--query", "nursing", "-o", "tsv"]
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["output_fmt"] == "tsv"


def test_json_search_excludes_response_metadata():
    payload = {
        "total": {"value": 77, "relation": "Eq"},
        "results": [],
        "searchTookMs": 28,
        "view": "Summary",
        "synonyms": {"keywords": []},
    }
    assert search.project_search_json(payload) == {"total": 77, "results": []}


@pytest.mark.parametrize("total", [77, 0])
def test_total_displayed_in_all_formats(capsys, total):
    payload = {"total": {"value": total, "relation": "Eq"}, "results": []}
    assert search.project_search_json(payload)["total"] == total
    search.print_search_results(payload)
    assert capsys.readouterr().out == f"Total results: {total}\n"
    search.print_search_tsv(payload)
    captured = capsys.readouterr()
    assert (
        captured.out == "@id\tceterms:ctid\tceterms:name\tceterms:description\t@type\n"
    )
    assert captured.err == f"Total results: {total}\n"


def test_total_is_not_current_page_size(capsys):
    payload = {
        "total": {"value": 77},
        "results": [{"ctid": "ce-example", "name": "Nursing"}],
    }
    search.print_search_results(payload)
    assert "Total results: 77" in capsys.readouterr().out
    search.print_search_tsv(payload)
    assert capsys.readouterr().err == "Total results: 77\n"

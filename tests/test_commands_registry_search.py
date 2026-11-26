from urllib.parse import parse_qs, urlsplit

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


@pytest.mark.parametrize("option", ["-o", "--output"])
def test_json_output_option(monkeypatch, option):
    calls = []
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    result = CliRunner().invoke(
        search.search_group, ["--query", "nursing", option, "json"]
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["output_fmt"] == "json"


def test_tsv_option(monkeypatch):
    calls = []
    monkeypatch.setattr(search, "execute_search", lambda ctx, **kw: calls.append(kw))
    result = CliRunner().invoke(
        search.search_group, ["--query", "nursing", "-o", "tsv"]
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["output_fmt"] == "tsv"

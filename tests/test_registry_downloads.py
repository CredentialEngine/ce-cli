"""Tests for Registry download commands, without a live API."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import click
import httpx2
import pytest
from click.testing import CliRunner

from ce.commands.registry import registry_group
from ce.registry import downloads

pytestmark = pytest.mark.unit


def test_commands_forward_arguments(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute",
        lambda *a, **kw: calls.append((a[1:], kw)),
    )
    runner = CliRunner()
    for args in (
        ["show", "--version", "2026-11-25"],
        [
            "get",
            "--class-name",
            "full",
            "--version",
            "latest",
            "--target-location",
            str(tmp_path),
        ],
        ["search", "show", "job"],
        [
            "search",
            "get",
            "--url",
            "https://api.example/exports/files/n/a.zip",
            "--target-location",
            str(tmp_path),
        ],
    ):
        result = runner.invoke(registry_group, ["downloads", *args])
        assert result.exit_code == 0, result.output
    assert calls[0] == (("show", "2026-11-25"), {})
    assert calls[1][1]["target_location"] == tmp_path
    assert calls[-1][1]["target_location"] == tmp_path
    assert calls[-1][1]["search"] is True
    assert calls[-1][0] == ("get", None)


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/exports/files/n/a.zip",
        "https://api.example/exports/files/n/b.zip",
        "https://api.example/exports/files/n/a.zip?x=1",
    ],
)
def test_unexpected_download_urls(url):
    with pytest.raises(click.ClickException):
        downloads.download_parts("https://api.example", url, "a.zip")


def test_download_parts():
    assert downloads.download_parts(
        "https://api.example", "/exports/files/nonce/my%20archive.zip", "my archive.zip"
    ) == ("nonce", "my archive.zip")


@pytest.mark.parametrize("name", ["../a.zip", "a\\b.zip", "CON.zip", "C:evil.zip"])
def test_unsafe_names(name):
    with pytest.raises(click.ClickException):
        downloads.safe_name(name)


def test_stream_without_api_token(monkeypatch, tmp_path):
    api = SimpleNamespace(
        export_download_without_preload_content=AsyncMock(
            return_value=httpx2.Response(
                302, headers={"location": "https://blob.example/archive?sig=secret"}
            )
        )
    )

    def handler(request):
        assert "authorization" not in request.headers
        assert request.headers["User-Agent"] == downloads.USER_AGENT
        return httpx2.Response(200, content=b"archive bytes")

    original = httpx2.AsyncClient
    monkeypatch.setattr(
        downloads.httpx2,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx2.MockTransport(handler), **kwargs),
    )
    archive = downloads.Archive("a.zip", "https://api.example/exports/files/n/a.zip")
    path = tmp_path / "a.zip"
    asyncio.run(
        downloads.download_archive(api, "https://api.example", archive, path, False)
    )
    assert path.read_bytes() == b"archive bytes"
    with pytest.raises(click.ClickException, match="already exists"):
        asyncio.run(
            downloads.download_archive(api, "https://api.example", archive, path, False)
        )
    assert api.export_download_without_preload_content.await_count == 1


@pytest.mark.parametrize("command", ["show", "get"])
def test_registry_version_option(monkeypatch, command):
    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute", lambda *a, **kw: calls.append(a[1:])
    )
    runner = CliRunner()
    for args, expected in [([], "latest"), (["--version", "2026-11-25"], "2026-11-25")]:
        result = runner.invoke(
            registry_group,
            [
                "downloads",
                command,
                *(["--class-name", "full"] if command == "get" else []),
                *args,
            ],
        )
        assert result.exit_code == 0, result.output
        assert calls[-1] == (command, expected)
    result = runner.invoke(registry_group, ["downloads", command, "latest"])
    assert result.exit_code == 2


def test_unsupported_registry_list_is_not_registered():
    runner = CliRunner()
    result = runner.invoke(registry_group, ["downloads", "--help"])
    assert result.exit_code == 0
    assert "list" not in registry_group.commands["downloads"].commands
    result = runner.invoke(registry_group, ["downloads", "list"])
    assert result.exit_code == 2
    assert "No such command" in result.output
    assert (
        "list" not in registry_group.commands["downloads"].commands["search"].commands
    )
    assert (
        runner.invoke(registry_group, ["downloads", "search", "list", "job"]).exit_code
        == 2
    )


def test_manifest_table(capsys):
    archive = SimpleNamespace(
        path="full/a.zip", file_count=12, download_url="/exports/files/n/a.zip"
    )
    manifest = SimpleNamespace(
        generated_at=None,
        folders=[
            SimpleNamespace(
                folder="full", type=None, file_count=12, zip_count=1, archives=[archive]
            ),
            SimpleNamespace(
                folder="credential",
                type="ceterms:Credential",
                file_count=12,
                zip_count=1,
                archives=[],
            ),
        ],
    )
    downloads.show_registry_manifest(
        manifest, {"ceterms:Credential": "Credential"}, "https://api.example"
    )
    output = capsys.readouterr().out
    assert "All Registry Data" in output
    assert "ceterms:Credential" in output
    assert "https://api.example/exports/files/n/a.zip" in output
    assert "JSON-LD files" in output


def test_target_location_default(monkeypatch):
    from pathlib import Path

    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute", lambda *a, **kw: calls.append(kw)
    )
    runner = CliRunner()
    for args in (
        ["get", "--class-name", "full"],
        ["search", "get", "--url", "https://api.example/exports/files/n/a.zip"],
    ):
        result = runner.invoke(registry_group, ["downloads", *args])
        assert result.exit_code == 0, result.output
        assert calls[-1]["target_location"] == Path(".")


def test_get_requires_explicit_selection(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "ce.commands.registry_downloads.execute", lambda *a, **kw: calls.append(kw)
    )
    runner = CliRunner()
    for args in (
        ["get"],
        ["get", "--url", "x", "--class-name", "full"],
        ["search", "get"],
        ["search", "get", "job", "--url", "x"],
    ):
        assert runner.invoke(registry_group, ["downloads", *args]).exit_code == 2
    assert not calls
    result = runner.invoke(
        registry_group, ["downloads", "get", "--url", "a", "--url", "b"]
    )
    assert result.exit_code == 0
    assert calls[-1]["urls"] == ("a", "b")


def test_select_classes():
    def folder(name, term):
        return SimpleNamespace(
            folder=name,
            type=term,
            archives=[
                SimpleNamespace(
                    path=name + "/a.zip",
                    download_url="/exports/files/n/a.zip",
                    file_count=1,
                )
            ],
        )

    manifest = SimpleNamespace(
        folders=[folder("full", None), folder("credential", "ceterms:Credential")]
    )
    assert [a.folder for a in downloads.select_classes(manifest, ["full"])] == ["full"]
    assert [
        a.folder for a in downloads.select_classes(manifest, ["ceterms:Credential"])
    ] == ["credential"]
    with pytest.raises(click.ClickException):
        downloads.select_classes(manifest, ["unknown"])


def test_direct_urls():
    url = "https://api.example/exports/files/n/a.zip"
    assert len(downloads.archives_from_urls("https://api.example", [url, url])) == 1
    with pytest.raises(click.ClickException):
        downloads.archives_from_urls(
            "https://api.example", [url, "https://evil.example/exports/files/n/b.zip"]
        )


def test_display_class_selection():
    folder = SimpleNamespace(
        folder="credential",
        type="ceterms:Credential",
        archives=[
            SimpleNamespace(
                path="credential/a.zip",
                download_url="/exports/files/n/a.zip",
                file_count=1,
            )
        ],
    )
    manifest = SimpleNamespace(folders=[folder])
    assert (
        downloads.select_classes(
            manifest, ["Credential"], {"ceterms:Credential": "Credential"}
        )[0].name
        == "a.zip"
    )


@pytest.mark.parametrize("option", ["--registry-url", "--consumer-url"])
def test_registry_rejects_url_override(option):
    result = CliRunner().invoke(
        registry_group, [option, "https://untrusted.example", "downloads", "show"]
    )
    assert result.exit_code == 2
    assert "No such option" in result.output

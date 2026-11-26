import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import click
import httpx2
import pytest
from consumer_api_client.exceptions import ApiException

from ce.registry import downloads

pytestmark = pytest.mark.unit


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


BASE = "https://api.example"


URL = BASE + "/exports/files/nonce/a.zip"


@pytest.fixture
def registry_sdk(monkeypatch):
    api = SimpleNamespace()
    client = AsyncMock()
    client.__aenter__.return_value = client
    monkeypatch.setattr(downloads, "ApiClient", Mock(return_value=client))
    monkeypatch.setattr(
        downloads,
        "require_environment",
        lambda: (
            "sandbox",
            SimpleNamespace(consumer_api_base="https://api.example", ssl_verify=True),
        ),
    )
    monkeypatch.setattr(downloads, "require_api_token", Mock(return_value="fixture"))
    monkeypatch.setattr(
        "ce.registry.api.require_api_token", Mock(return_value="fixture")
    )
    monkeypatch.setattr(downloads, "ExportApi", Mock(return_value=api))
    monkeypatch.setattr(downloads, "SchemaApi", Mock(return_value=api))
    return api, client


def manifest():
    archive = SimpleNamespace(path="credential/a.zip", download_url=URL, file_count=4)
    folder = SimpleNamespace(
        folder="credential",
        type="ceterms:Credential",
        archives=[archive],
        file_count=None,
        zip_count=None,
    )
    return SimpleNamespace(
        folders=[folder], generated_at=datetime(2026, 1, 1, tzinfo=UTC)
    )


@pytest.mark.parametrize("status", ["Running", "Completed"])
def test_export_status(registry_sdk, capsys, status):
    api, client = registry_sdk
    response = httpx2.Response(200, json={"status": status})
    api.export_get_search_export_without_preload_content = AsyncMock(
        return_value=response
    )
    api.export_get_search_export_downloads = AsyncMock(
        return_value=[SimpleNamespace(file_name="a.zip", download_url=URL)]
    )
    downloads.execute(None, "show", "job", search=True)
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == status
    assert response.is_closed
    assert client.user_agent == downloads.USER_AGENT
    if status == "Completed":
        assert payload["files"] == [{"fileName": "a.zip", "downloadUrl": URL}]
        api.export_get_search_export_downloads.assert_awaited_once()
    else:
        assert "files" not in payload
        api.export_get_search_export_downloads.assert_not_awaited()


def test_manifest_show(registry_sdk, capsys):
    api, _ = registry_sdk
    api.export_get_downloads = AsyncMock(return_value=manifest())
    api.schema_get_labels = AsyncMock(return_value={"ceterms:Credential": "Credential"})
    downloads.execute(None, "show", "latest")
    out = capsys.readouterr().out
    assert "Last generated: 2026-01-01" in out
    assert "ceterms:Credential" in out and URL in out
    assert api.schema_get_labels.await_args.kwargs["request_body"] == [
        "ceterms:Credential"
    ]


@pytest.mark.parametrize(
    "options",
    [
        {"urls": (URL,)},
        {"classes": ("Credential",)},
        {"class_names": ("ceterms:Credential",)},
    ],
)
def test_download_selection(registry_sdk, monkeypatch, tmp_path, options):
    api, _ = registry_sdk
    api.export_get_downloads = AsyncMock(return_value=manifest())
    api.schema_get_labels = AsyncMock(return_value={"ceterms:Credential": "Credential"})
    save = AsyncMock()
    monkeypatch.setattr(downloads, "save_archives", save)
    downloads.execute(None, "get", "latest", target_location=tmp_path, **options)
    assert save.await_args.args[2][0].url == URL
    assert save.await_args.kwargs["target_location"] == tmp_path
    assert api.export_get_downloads.await_count == (0 if "urls" in options else 1)
    assert api.schema_get_labels.await_count == (1 if "classes" in options else 0)


@pytest.mark.parametrize(
    "error,match",
    [
        (ApiException(status=409), "not ready"),
        (httpx2.ConnectError("offline"), "Could not reach"),
    ],
)
def test_manifest_error(registry_sdk, error, match):
    api, _ = registry_sdk
    api.export_get_downloads = AsyncMock(side_effect=error)
    with pytest.raises(click.ClickException, match=match):
        downloads.execute(None, "show", "latest")


def test_collision_paths(monkeypatch, tmp_path):
    save = AsyncMock()
    monkeypatch.setattr(downloads, "download_archive", save)
    archives = [downloads.Archive("a.zip", URL, folder) for folder in ("one", "two")]
    asyncio.run(downloads.save_archives(None, BASE, archives, tmp_path))
    assert [c.args[3] for c in save.await_args_list] == [
        tmp_path / f / "a.zip" for f in ("one", "two")
    ]
    save.reset_mock()
    with pytest.raises(click.ClickException, match="Duplicate"):
        asyncio.run(downloads.save_archives(None, BASE, archives[:1] * 2, tmp_path))
    save.assert_not_awaited()


@pytest.mark.parametrize(
    "response,match",
    [
        (httpx2.Response(410), "redemption failed"),
        (
            httpx2.Response(302, headers={"location": "http://storage.example/a.zip"}),
            "Invalid storage redirect",
        ),
    ],
)
def test_download_rejects_bad_redemption(tmp_path, response, match):
    api = SimpleNamespace(
        export_download_without_preload_content=AsyncMock(return_value=response)
    )
    with pytest.raises(click.ClickException, match=match):
        asyncio.run(
            downloads.download_archive(
                api, BASE, downloads.Archive("a.zip", URL), tmp_path / "a.zip", False
            )
        )
    assert response.is_closed
    assert not list(tmp_path.iterdir())

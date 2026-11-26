"""Consumer API export discovery and streamed downloads."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urljoin, urlsplit

import click
import httpx2
from consumer_api_client import ApiClient, Configuration
from consumer_api_client.api.export_api import ExportApi
from consumer_api_client.api.schema_api import SchemaApi
from consumer_api_client.exceptions import ApiException

from ce.auth.api_session import require_api_token
from ce.config.context import require_environment
from ce.registry.api import AuthenticatedApi
from ce.utils.download_progress import DownloadProgress, content_length
from ce.utils.user_agent import USER_AGENT

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Archive:
    name: str
    url: str | None
    folder: str = ""
    count: int | None = None


def registry_archives(manifest):
    return [
        Archive(PurePosixPath(a.path).name, a.download_url, f.folder, a.file_count)
        for f in manifest.folders or []
        for a in f.archives or []
    ]


def safe_name(name: str) -> str:
    if (
        not name
        or name in {".", ".."}
        or name[-1] in ". "
        or any(c in name for c in '/\\:<>"|?*')
        or any(ord(c) < 32 for c in name)
        or name.split(".")[0].upper()
        in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
    ):
        raise click.ClickException("Unsafe archive or folder name returned by API.")
    return name


def download_parts(base: str, url: str, expected_name: str) -> tuple[str, str]:
    target = urlsplit(urljoin(base.rstrip("/") + "/", url))
    origin = urlsplit(base)
    prefix = origin.path.rstrip("/") + "/exports/files/"
    if (
        target.scheme != origin.scheme
        or target.netloc != origin.netloc
        or not target.path.startswith(prefix)
        or target.query
        or target.fragment
    ):
        raise click.ClickException("Unexpected Consumer API download URL.")
    parts = target.path[len(prefix) :].split("/")
    if len(parts) != 2:
        raise click.ClickException("Invalid Consumer API download path.")
    nonce, name = map(unquote, parts)
    if not nonce or "/" in nonce or "\\" in nonce or name != expected_name:
        raise click.ClickException("Invalid download identifier.")
    return nonce, safe_name(name)


async def download_archive(
    api: ExportApi, base: str, archive: Archive, path: Path, overwrite: bool
) -> None:
    if path.exists() and not overwrite:
        raise click.ClickException(f"File already exists: {path}.")
    if not archive.url:
        raise click.ClickException(f"No download URL available for {archive.name}.")
    nonce, name = download_parts(base, archive.url, archive.name)
    response = await api.export_download_without_preload_content(
        nonce, name, _request_timeout=60.0
    )
    try:
        if response.status_code != 302:
            raise click.ClickException(
                f"Download redemption failed (HTTP {response.status_code}). Request a fresh download listing and retry."
            )
        blob = response.headers.get("location", "")
    finally:
        await response.aclose()
    target = urlsplit(blob)
    if (
        target.scheme != "https"
        or not target.hostname
        or target.username
        or target.password
    ):
        raise click.ClickException("Invalid storage redirect returned by Consumer API.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        # Separate unauthenticated client: never send the API bearer token to storage.
        async with (
            httpx2.AsyncClient(
                timeout=120.0,
                follow_redirects=False,
                headers={"User-Agent": USER_AGENT},
            ) as client,
            client.stream("GET", blob) as stream,
        ):
            if stream.status_code != 200:
                raise click.ClickException(
                    f"Storage download failed (HTTP {stream.status_code})."
                )
            with NamedTemporaryFile(
                dir=path.parent, prefix=".ce-download-", delete=False
            ) as out:
                temp = Path(out.name)
                with DownloadProgress(
                    archive.name, content_length(stream.headers)
                ) as progress:
                    async for chunk in stream.aiter_bytes(1024 * 1024):
                        out.write(chunk)
                        progress.advance(len(chunk))
        if overwrite:
            temp.replace(path)
        else:
            # Reserve the destination atomically without overwriting another process's file.
            os.link(temp, path)
        click.echo(f"Downloaded {path} — {progress.summary()}")
    except httpx2.HTTPError:
        raise click.ClickException(
            "Storage connection failed. Retry to obtain a fresh download URL."
        ) from None
    except OSError as exc:
        raise click.ClickException(
            f"Could not save {path}: {exc.strerror or type(exc).__name__}"
        ) from None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def archives_from_urls(base, urls):
    archives = []
    seen = set()
    for url in urls:
        name = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
        nonce, name = download_parts(base, url, name)
        key = (nonce, name)
        if key not in seen:
            seen.add(key)
            archives.append(Archive(name, url))
    return archives


def class_value(folder, labels):
    term = "full" if folder.folder.lower() == "full" else folder.type or folder.folder
    if labels is None:
        return term
    return "All Registry Data" if term == "full" else labels.get(term, term)


def select_classes(manifest, classes, labels=None):
    selected = []
    for term in dict.fromkeys(classes):
        matches = [
            f
            for f in manifest.folders or []
            if (class_value(f, labels).casefold() == term.casefold())
        ]
        if len(matches) > 1:
            raise click.ClickException(
                f"Ambiguous export class: {term}. Use --class-name."
            )
        if not matches:
            raise click.ClickException(
                f"Unknown export class: {term}. Use downloads show to list classes."
            )
        for folder in matches:
            for a in folder.archives or []:
                archive = Archive(
                    PurePosixPath(a.path).name,
                    a.download_url,
                    folder.folder,
                    a.file_count,
                )
                if archive not in selected:
                    selected.append(archive)
    return selected


async def save_archives(api, base, archives, target_location):
    if not archives:
        raise click.ClickException("No archives available.")
    paths = [(a, target_location / safe_name(a.name)) for a in archives]
    # Preserve class directories only when archive names collide.
    if len({p.name.casefold() for _, p in paths}) != len(paths):
        paths = [
            (
                a,
                target_location / safe_name(a.folder) / safe_name(a.name)
                if a.folder
                else target_location / safe_name(a.name),
            )
            for a in archives
        ]
    if len({str(p).casefold() for _, p in paths}) != len(paths):
        raise click.ClickException("Duplicate archive destinations returned by API.")
    for _, path in paths:
        if path.exists():
            raise click.ClickException(f"File already exists: {path}.")
    for a, path in paths:
        await download_archive(api, base, a, path, False)


def print_table(headers, rows):
    rows = [tuple(str(value) for value in row) for row in rows]
    widths = [
        max(len(h), *(len(row[i]) for row in rows)) if rows else len(h)
        for i, h in enumerate(headers)
    ]

    def line(row):
        return "  ".join(
            value.ljust(width) for value, width in zip(row, widths)
        ).rstrip()

    click.echo(line(headers))
    click.echo(line(tuple("-" * width for width in widths)))
    for row in rows:
        click.echo(line(row))


def format_count(value):
    return f"{value:,}" if value is not None else "-"


def show_registry_manifest(manifest, labels, base):
    if manifest.generated_at is not None:
        click.echo(f"Last generated: {manifest.generated_at.isoformat()}")
    folders = sorted(
        manifest.folders or [],
        key=lambda f: (
            f.folder.lower() != "full",
            labels.get(f.type or f.folder, f.type or f.folder).casefold(),
        ),
    )
    rows = []
    links = []
    for folder in folders:
        full = folder.folder.lower() == "full"
        term = folder.type or folder.folder
        label = "All Registry Data" if full else labels.get(term, term)
        archives = folder.archives or []
        count = folder.file_count
        if count is None and all(a.file_count is not None for a in archives):
            count = sum(a.file_count for a in archives)
        rows.append(
            (
                label,
                "full" if full else term,
                format_count(count),
                format_count(
                    folder.zip_count if folder.zip_count is not None else len(archives)
                ),
            )
        )
        for archive in archives:
            links.append(
                (
                    label,
                    PurePosixPath(archive.path).name,
                    format_count(archive.file_count),
                    urljoin(base.rstrip("/") + "/", archive.download_url)
                    if archive.download_url
                    else "-",
                )
            )
    click.echo()
    print_table(("Class", "Class name", "JSON-LD files", "ZIP files"), rows)
    click.echo("\nArchives (one-time download links):")
    print_table(("Class", "File", "Count", "Download URL"), links)


def show_archives(archives, base):
    print_table(
        ("File", "Count", "Download URL"),
        [
            (
                a.name,
                format_count(a.count),
                urljoin(base.rstrip("/") + "/", a.url) if a.url else "-",
            )
            for a in archives
        ],
    )


def execute(ctx, operation, identifier, *, search=False, **options):
    urls = options.pop("urls", ())
    classes = options.pop("classes", ())
    class_names = options.pop("class_names", ())
    if operation == "get" and sum(map(bool, (urls, classes, class_names))) != 1:
        raise click.UsageError(
            "Select archive URLs, class labels or schema class names explicitly."
        )
    env_name, env = require_environment()
    token = require_api_token(env_name)
    base = (env.consumer_api_base or "").rstrip("/")
    url = urlsplit(base)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise click.UsageError("Consumer API base URL is not configured correctly.")

    async def run(token):
        config = Configuration(host=base, access_token=token, verify_ssl=env.ssl_verify)
        async with ApiClient(config) as client:
            client.user_agent = USER_AGENT
            api = AuthenticatedApi(ExportApi(client), config, env_name)
            if operation == "get" and urls:
                await save_archives(
                    api, base, archives_from_urls(base, urls), **options
                )
                return
            if search and operation == "show":
                # Swagger does not declare the 200 response body; use SDK raw response.
                response = await api.export_get_search_export_without_preload_content(
                    identifier, _request_timeout=60.0
                )
                try:
                    if response.status_code == 401:
                        raise ApiException(status=401)
                    if response.status_code != 200:
                        raise click.ClickException(
                            f"Search export status failed (HTTP {response.status_code})."
                        )
                    await response.aread()
                    status = response.json()
                finally:
                    await response.aclose()
                if status.get("status", "").casefold() == "completed":
                    result = await api.export_get_search_export_downloads(
                        identifier, _request_timeout=60.0
                    )
                    status["files"] = [
                        {"fileName": a.file_name, "downloadUrl": str(a.download_url)}
                        for a in result
                    ]
                click.echo(json.dumps(status, indent=2, ensure_ascii=False))
                return
            if search:
                raise click.UsageError("Unsupported search download operation.")
            else:
                result = await api.export_get_downloads(
                    identifier, _request_timeout=60.0
                )
                if operation == "show" or classes:
                    terms = sorted(
                        {
                            f.type or f.folder
                            for f in result.folders or []
                            if f.folder.lower() != "full"
                        }
                    )
                    labels = (
                        await AuthenticatedApi(
                            SchemaApi(client), config, env_name
                        ).schema_get_labels(
                            language="en", request_body=terms, _request_timeout=60.0
                        )
                        if terms
                        else {}
                    )
                    if operation == "show":
                        show_registry_manifest(result, labels, base)
                        return
                else:
                    labels = None
                archives = select_classes(
                    result, classes or class_names, labels if classes else None
                )
            await save_archives(api, base, archives, **options)

    try:
        asyncio.run(run(token))
    except ApiException as exc:
        raise click.ClickException(
            f"Consumer API request failed (HTTP {exc.status})."
            + (" Export is not ready." if exc.status == 409 else "")
        ) from None
    except httpx2.HTTPError:
        raise click.ClickException("Could not reach Consumer API.") from None

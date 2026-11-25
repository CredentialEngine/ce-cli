"""What the `ce publisher` commands share: the options, the signed-in client and how an error is shown."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, NoReturn

import click

from ce.auth.token_manager import require_login
from ce.config.context import DEFAULT_ENVIRONMENTS, require_environment
from ce.implementations.publisher import service
from ce.implementations.publisher.client import (
    PublisherApiError,
    PublisherClient,
    resolve_publisher_url,
)
from ce.utils.display import new_console

console = new_console()
err_console = new_console(stderr=True)


def publisher_url_option(f):  # type: ignore[no-untyped-def]
    return click.option(
        "--publisher-url",
        default=None,
        metavar="URL",
        help="Publisher API address. Defaults to the environment's (or CE_PUBLISHER_API_URL).",
    )(f)


def project_option(f):  # type: ignore[no-untyped-def]
    return click.option(
        "--project-id", "project_id", required=True, type=int, help="The project's number."
    )(f)


def output_option(f):  # type: ignore[no-untyped-def]
    return click.option(
        "--output",
        "-o",
        "output",
        type=click.Choice(["text", "json"]),
        default="text",
        show_default=True,
        help="Output format.",
    )(f)


@contextmanager
def publisher_client(publisher_url: str | None) -> Iterator[PublisherClient]:
    """A Publisher client for the signed-in user, or exit 1 with the reason."""
    token = require_login()
    name, env = require_environment()
    default = DEFAULT_ENVIRONMENTS.get(name)
    environment_url = env.publisher_api_base or (default.publisher_api_base if default else "")

    try:
        url = resolve_publisher_url(publisher_url, environment_url, name)
    except PublisherApiError as exc:
        fail(str(exc))

    with PublisherClient(url, token, verify=env.ssl_verify) as client:
        try:
            yield client
        except PublisherApiError as exc:
            fail(describe_error(exc))


def describe_error(exc: PublisherApiError) -> str:
    if exc.status_code == 401:
        return f"{exc} Your session may have expired; run 'ce login'."
    if exc.status_code == 403 and not exc.detail:
        # A 403 with no message means the account does not have the Publisher user role. A 403 that comes with a
        # message (for example, only the project's author may change it) is shown as it is, by the line below.
        return f"{exc} Your account needs the Publisher user role."
    return str(exc)


def fail(message: str) -> NoReturn:
    err_console.print(f"Error: {message}", highlight=False, soft_wrap=True)
    sys.exit(1)


def echo_json(value: Any) -> None:
    click.echo(json.dumps(value, indent=2))


def print_validation_status(summary: service.ValidationSummary, *, verbose: bool) -> None:
    if not summary.validated:
        hint = (
            "Validation is running."
            if summary.status == service.VALIDATING
            else "Validation has not been run on it yet."
        )
        console.print(
            f"Iteration {summary.iteration_id}: {summary.status}, "
            f"{len(summary.files)} file(s). {hint}",
            highlight=False,
        )
        return

    console.print(
        f"Iteration {summary.iteration_id}: {len(summary.valid_files)} succeeded, "
        f"{len(summary.files_with_errors)} with errors.",
        highlight=False,
    )

    if not verbose:
        return

    failed = set(summary.files_with_errors)
    for name in summary.files:
        mark = "FAIL" if name in failed else "ok  "
        console.print(f"  {mark}  {name}", highlight=False, soft_wrap=True)
        for finding in summary.findings:
            if finding.file_name == name:
                console.print(
                    f"      {service.format_finding(finding, with_file=False)}",
                    highlight=False,
                    soft_wrap=True,
                )

"""Registry download commands, independent of Registry search."""

from pathlib import Path

import click


def execute(*args, **kwargs):
    # Import transfer code only when executing a download-related command.
    from ce.registry.downloads import execute as run_download

    return run_download(*args, **kwargs)


@click.group("downloads")
def downloads():
    """Inspect and download completed Registry exports."""


@downloads.group("search")
def search():
    """Inspect search exports by job ID or download by URL."""


def target_location_option(fn):
    return click.option(
        "--target-location",
        type=click.Path(file_okay=False, path_type=Path),
        default=Path("."),
        show_default=True,
    )(fn)


@downloads.command("show")
@click.option(
    "--version",
    "date_or_latest",
    default="latest",
    show_default=True,
    help="Export version: latest or a UTC date (YYYY-MM-DD).",
)
@click.pass_context
def show_registry(ctx, date_or_latest):
    """Show Registry classes, counts and archive download links."""
    execute(ctx, "show", date_or_latest)


@downloads.command("get")
@click.option(
    "--version",
    "date_or_latest",
    default="latest",
    show_default=True,
    help="Export version: latest or a UTC date (YYYY-MM-DD).",
)
@click.option(
    "--url",
    "urls",
    multiple=True,
    help="Archive download URL. Repeat for multiple files.",
)
@click.option(
    "--class",
    "classes",
    multiple=True,
    help="Class label from show (e.g. Credential). Repeatable.",
)
@click.option(
    "--class-name",
    "class_names",
    multiple=True,
    help="Schema class name from show (e.g. ceterms:Credential or full). Repeatable.",
)
@target_location_option
@click.pass_context
def get_registry(ctx, date_or_latest, target_location, urls, classes, class_names):
    """Download Registry export archives to disk."""
    if sum(map(bool, (urls, classes, class_names))) != 1:
        raise click.UsageError(
            "Specify exactly one of --url, --class or --class-name. Use downloads show to find links and classes."
        )
    execute(
        ctx,
        "get",
        date_or_latest,
        target_location=target_location,
        urls=urls,
        classes=classes,
        class_names=class_names,
    )


@search.command("show")
@click.argument("job_id")
@click.pass_context
def show_search(ctx, job_id):
    """Show your search export status and one-time links when completed."""
    execute(ctx, "show", job_id, search=True)


@search.command("get")
@click.option(
    "--url",
    "urls",
    multiple=True,
    required=True,
    help="Archive download URL. Repeat for multiple files.",
)
@target_location_option
@click.pass_context
def get_search(ctx, target_location, urls):
    """Download completed search export archives to disk."""
    execute(ctx, "get", None, search=True, target_location=target_location, urls=urls)

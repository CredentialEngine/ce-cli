"""Output formatting utilities.

Mirrors az's --output / -o flag:
  table   - plain aligned columns (default)
  json    - pretty-printed JSON
  yaml    - YAML (requires pyyaml)
  tsv     - tab-separated values, script-friendly
  none    - suppress output (useful in scripts)
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import click

from ce.utils.display import new_console, plain_table

console = new_console()

OutputFormat = str  # "table" | "json" | "yaml" | "tsv" | "none"

OUTPUT_FORMATS = ("table", "json", "yaml", "tsv", "none")


def print_output(
    data: Any,
    fmt: OutputFormat,
    *,
    columns: Sequence[str] | None = None,
    title: str | None = None,
) -> None:
    if fmt == "none":
        return

    if fmt == "json":
        _print_json(data)
    elif fmt == "yaml":
        _print_yaml(data)
    elif fmt == "tsv":
        _print_tsv(data, columns=columns)
    else:
        _print_table(data, columns=columns, title=title)


def _print_json(data: Any) -> None:
    click.echo(json.dumps(data, indent=2, default=str))


def _print_yaml(data: Any) -> None:
    try:
        import yaml  # type: ignore
    except ImportError:
        click.echo(json.dumps(data, indent=2, default=str))
        return
    click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True), nl=False)


def _print_tsv(data: Any, columns: Sequence[str] | None) -> None:
    rows = _to_rows(data)
    if not rows:
        return
    cols = list(columns) if columns else list(rows[0].keys())
    for row in rows:
        click.echo("\t".join(str(row.get(c, "")) for c in cols))


def _print_table(
    data: Any,
    columns: Sequence[str] | None,
    title: str | None,
) -> None:
    rows = _to_rows(data)
    if not rows:
        console.print("No results.")
        return

    cols = list(columns) if columns else list(rows[0].keys())

    table = plain_table([col.replace("_", " ").title() for col in cols])

    for row in rows:
        table.add_row(*[str(row.get(c, "-")) for c in cols])

    if title:
        console.print(title)
    console.print()
    console.print(table)
    console.print()


def _to_rows(data: Any) -> list[dict]:
    """Normalise data to a list of dicts."""
    if isinstance(data, list):
        return [r if isinstance(r, dict) else {"value": r} for r in data]
    if isinstance(data, dict):
        return [data]
    return [{"value": data}]


def output_option(f):  # type: ignore[no-untyped-def]
    """Decorator that adds ``-o / --output`` to a Click command."""
    return click.option(
        "-o",
        "--output",
        "output_fmt",
        type=click.Choice(OUTPUT_FORMATS, case_sensitive=False),
        default=None,
        show_default=True,
        help="Output format.",
        envvar="CE_OUTPUT",
    )(f)


def resolve_output_fmt(output_fmt: str | None) -> OutputFormat:
    """Return the effective output format, checking config if not passed."""
    if output_fmt:
        return output_fmt
    from ce.config.context import load_cli_config

    return load_cli_config().output_format or "table"

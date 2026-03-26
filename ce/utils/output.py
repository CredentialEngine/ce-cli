"""Output formatting utilities.

Mirrors az's --output / -o flag:
  table   - human-friendly Rich table (default)
  json    - pretty-printed JSON
  yaml    - YAML (requires pyyaml)
  tsv     - tab-separated values, script-friendly
  none    - suppress output (useful in scripts)
"""

from __future__ import annotations

import json
from typing import Any, Sequence

import click
from rich.console import Console
from rich.table import Table, box

console = Console()

OutputFormat = str   # "table" | "json" | "yaml" | "tsv" | "none"

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
    from rich.syntax import Syntax
    text = json.dumps(data, indent=2, default=str)
    console.print(Syntax(text, "json", theme="ansi_dark", background_color="default"))


def _print_yaml(data: Any) -> None:
    try:
        import yaml  # type: ignore
    except ImportError:
        click.echo(json.dumps(data, indent=2, default=str))
        return
    from rich.syntax import Syntax
    text = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    console.print(Syntax(text, "yaml", theme="ansi_dark", background_color="default"))


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
        console.print("[dim]No results.[/dim]")
        return

    cols = list(columns) if columns else list(rows[0].keys())

    table = Table(
        title=title,
        box=box.SIMPLE_HEAD,
        show_lines=False,
        header_style="bold",
        border_style="dim",
    )
    for col in cols:
        table.add_column(col.replace("_", " ").title())

    for row in rows:
        table.add_row(*[str(row.get(c, "—")) for c in cols])

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
        "-o", "--output",
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

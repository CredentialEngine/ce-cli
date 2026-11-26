"""Plain terminal output: no boxes, no colours, no highlighting.

Spinners (console.status) are the one piece of decoration the CLI keeps.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from rich.console import Console
from rich.table import Table


def new_console(*, stderr: bool = False) -> Console:
    """A console that prints text as written: no markup, no highlighting of numbers or paths, no emoji codes."""
    return Console(stderr=stderr, highlight=False, emoji=False, markup=False)


def plain_table(
    headers: Sequence[str], widths: Sequence[int | None] | None = None
) -> Table:
    """Columns separated by spaces, with a plain header row. No borders, rules or styles."""
    table = Table(
        box=None,
        show_edge=False,
        pad_edge=False,
        padding=(0, 2),
        header_style="none",
    )
    for index, header in enumerate(headers):
        width = widths[index] if widths else None
        table.add_column(header, overflow="fold", width=width)
    return table


def print_pairs(console: Console, pairs: Iterable[tuple[str, str]]) -> None:
    """Print `Key:  value` lines with the values aligned."""
    rows = [(key, value) for key, value in pairs]
    if not rows:
        return
    width = max(len(key) for key, _ in rows) + 1
    for key, value in rows:
        console.print(f"{(key + ':').ljust(width)}  {value}", soft_wrap=True)

from __future__ import annotations

import io
import re

import pytest
from rich.console import Console

from ce.utils.display import new_console, plain_table, print_pairs

pytestmark = pytest.mark.unit


ANSI = re.compile(r"\x1b\[")


BOX_CHARS = re.compile("[─-▟]")


def terminal_console(buffer: io.StringIO) -> Console:
    """A console that behaves like a colour terminal, so any styling would show up as escape codes."""
    return Console(
        file=buffer,
        force_terminal=True,
        color_system="truecolor",
        width=100,
        highlight=False,
    )


def assert_plain(text: str) -> None:
    assert not ANSI.search(text), f"colour or style codes in output: {text!r}"
    assert not BOX_CHARS.search(text), f"box characters in output: {text!r}"


def test_plain_table_has_no_borders_or_styles() -> None:
    buffer = io.StringIO()
    table = plain_table(["Name", "Label"])
    table.add_row("sandbox", "Sandbox")
    terminal_console(buffer).print(table)

    text = buffer.getvalue()
    assert_plain(text)
    assert "Name" in text and "sandbox" in text


def test_plain_table_honours_column_widths() -> None:
    buffer = io.StringIO()
    table = plain_table(["#", "CTID"], widths=[4, 10])
    table.add_row("1", "ce-aaaaaaaaaaaaaaaaaaaa")
    terminal_console(buffer).print(table)

    text = buffer.getvalue()
    assert_plain(text)
    # The CTID column is 10 wide, so the value folds onto several lines instead of widening the table.
    assert "ce-aaaaaaaaaaaaaaaaaaaa" not in text
    assert text.replace("\n", "").replace(" ", "").endswith("ce-aaaaaaaaaaaaaaaaaaaa")


def test_the_console_prints_markup_and_numbers_as_written() -> None:
    buffer = io.StringIO()
    console = new_console()
    console.file = buffer
    console.print("[bold]kept as typed[/bold] 42 https://example.org/a")

    assert buffer.getvalue() == "[bold]kept as typed[/bold] 42 https://example.org/a\n"


def test_print_pairs_aligns_values_without_styling() -> None:
    buffer = io.StringIO()
    console = new_console()
    console.file = buffer
    print_pairs(console, [("Name", "x"), ("Publisher base", "y")])

    assert buffer.getvalue().splitlines() == [
        "Name:            x",
        "Publisher base:  y",
    ]

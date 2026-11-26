"""ce publisher project audit show"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import click

from ce.implementations.publisher.cli import (
    console,
    echo_json,
    output_option,
    project_option,
    publisher_client,
    publisher_url_option,
)


@click.command("show")
@project_option
@output_option
@publisher_url_option
def main(project_id: int, output: str, publisher_url: str | None) -> None:
    """Show who did what to the project, oldest first."""
    with publisher_client(publisher_url) as client:
        entries = client.get_audit(project_id)

    entries = sorted(
        entries, key=lambda item: (str(item.get("createdAt", "")), item.get("id", 0))
    )

    if output == "json":
        echo_json(entries)
        return

    for entry in entries:
        console.print(
            f"{_short_time(str(entry.get('createdAt', '')))}  "
            f"{entry.get('eventType', ''):<26} {entry.get('description', '')}",
            highlight=False,
            soft_wrap=True,
        )


def _short_time(value: str) -> str:
    """An ISO UTC time from the Publisher as 'yyyy-mm-dd hh:mm:ss UTC', or the value as given."""
    # The Publisher sends 7 digits after the seconds; Python's date parser accepts at most 6, so cut the rest.
    text = re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return value
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

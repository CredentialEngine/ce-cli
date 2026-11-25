"""ce publisher project validation errors show"""

from __future__ import annotations

import click

from ce.implementations.publisher import service
from ce.implementations.publisher.cli import (
    console,
    echo_json,
    output_option,
    print_validation_status,
    project_option,
    publisher_client,
    publisher_url_option,
)


@click.command("show")
@project_option
@output_option
@publisher_url_option
def main(project_id: int, output: str, publisher_url: str | None) -> None:
    """Show the validation errors that must be fixed before the project can be completed."""
    with publisher_client(publisher_url) as client:
        summary = service.validation_summary(client, project_id)

    if output == "json":
        echo_json([item for item in summary.as_dict()["findings"] if item["blocking"]])
        return

    if not summary.validated:
        print_validation_status(summary, verbose=False)
        return

    for finding in summary.errors:
        console.print(service.format_finding(finding), highlight=False, soft_wrap=True)
    count = len(summary.errors)
    console.print(f"{count} error{'' if count == 1 else 's'}", highlight=False, soft_wrap=True)

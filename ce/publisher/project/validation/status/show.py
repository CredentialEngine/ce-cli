"""ce publisher project validation status show"""

from __future__ import annotations

import click

from ce.implementations.publisher import service
from ce.implementations.publisher.cli import (
    echo_json,
    output_option,
    print_validation_status,
    project_option,
    publisher_client,
    publisher_url_option,
)


@click.command("show")
@project_option
@click.option("--verbose", "-v", is_flag=True, help="List every file and what was found in it.")
@output_option
@publisher_url_option
def main(project_id: int, verbose: bool, output: str, publisher_url: str | None) -> None:
    """Show how many files passed validation and how many have errors."""
    with publisher_client(publisher_url) as client:
        summary = service.validation_summary(client, project_id)

    if output == "json":
        result = summary.as_dict()
        if not verbose:
            result.pop("findings")
        echo_json(result)
        return

    print_validation_status(summary, verbose=verbose)

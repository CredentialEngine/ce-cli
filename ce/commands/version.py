"""Version command: ce version.

Prints version info for the CLI and (optionally) checks PyPI for a newer release.
"""

from __future__ import annotations

import click
from rich.console import Console

from ce import __version__

console = Console()
err_console = Console(stderr=True)


@click.command("version")
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Check for a newer version on PyPI.",
)
def version_command(check: bool) -> None:
    """Show the current CLI version."""
    console.print(f"ce version [bold]{__version__}[/bold]")

    if check:
        _check_for_update()


def _check_for_update() -> None:
    """Query PyPI for the latest published version of ce-cli."""
    import httpx

    try:
        with console.status("[dim]Checking for updates…[/dim]"):
            resp = httpx.get(
                "https://pypi.org/pypi/ce-cli/json",
                timeout=5,
                follow_redirects=True,
            )
        if not resp.is_success:
            console.print("[dim]Could not reach PyPI.[/dim]")
            return

        latest = resp.json()["info"]["version"]
    except Exception as exc:
        console.print(f"[dim]Update check failed: {exc}[/dim]")
        return

    if latest == __version__:
        console.print(f"[green]✓[/green] You are up to date.")
    else:
        console.print(
            f"[yellow]⚠[/yellow]  A newer version is available: "
            f"[bold]{latest}[/bold]  (you have {__version__})\n"
            f"  Upgrade with: [bold]pip install --upgrade ce-cli[/bold]"
        )
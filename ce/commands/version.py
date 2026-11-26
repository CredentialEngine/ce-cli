"""Version command: ce version.

Prints version info for the CLI and (optionally) checks PyPI for a newer release.
"""

from __future__ import annotations

import click

from ce import __version__
from ce.utils.display import new_console
from ce.utils.user_agent import USER_AGENT

console = new_console()
err_console = new_console(stderr=True)


@click.command("version")
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Check for a newer version on PyPI.",
)
def version_command(check: bool) -> None:
    """Show the current CLI version."""
    console.print(f"ce version {__version__}")

    if check:
        _check_for_update()


def _check_for_update() -> None:
    """Query PyPI for the latest published version of ce-cli."""
    import httpx2

    try:
        with console.status("Checking for updates…"):
            resp = httpx2.get(
                "https://pypi.org/pypi/ce-cli/json",
                timeout=5,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
            )
        if not resp.is_success:
            console.print("Could not reach PyPI.")
            return

        latest = resp.json()["info"]["version"]
    except (httpx2.HTTPError, ValueError, KeyError, TypeError) as exc:
        console.print(f"Update check failed: {exc}")
        return

    if latest == __version__:
        console.print("You are up to date.")
    else:
        console.print(
            f"Warning: A newer version is available: "
            f"{latest}  (you have {__version__})\n"
            f"  Upgrade with: pip install --upgrade ce-cli"
        )

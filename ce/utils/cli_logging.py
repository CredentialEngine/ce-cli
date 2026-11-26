"""Root version banner and leaf log-level options, following ceops."""

from __future__ import annotations

from typing import Any

import click

from ce import __version__
from ce.utils.logging import VALID_LOG_LEVELS


class VersionedGroup(click.Group):
    """Display the version as CLI output, independently of logging."""

    @staticmethod
    def _requests_root_version(cli_args: list[str]) -> bool:
        """Distinguish root --version from a leaf command's --version option."""
        return bool(cli_args and cli_args[0] == "--version")

    def main(self, *args: Any, **kwargs: Any) -> Any:
        cli_args = kwargs.get("args")
        if cli_args is None and args:
            cli_args = args[0]
        if cli_args is None:
            import sys

            cli_args = sys.argv[1:]
        # Click itself prints the version for the root --version option.
        if not self._requests_root_version(cli_args):
            click.echo(f"ce, version {__version__}", err=True)
        return super().main(*args, **kwargs)


class LogLevelChoice(click.Choice):
    """Case-insensitive log levels with actionable validation feedback."""

    def __init__(self) -> None:
        super().__init__(VALID_LOG_LEVELS, case_sensitive=False)

    def convert(
        self,
        value: str | None,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> str:
        try:
            return super().convert(value, param, ctx)
        except click.BadParameter:
            raise click.BadParameter(
                f"Invalid log level {value!r}. Choose one of: "
                f"{', '.join(VALID_LOG_LEVELS)}. "
                "Level names are case-insensitive. "
                "Example: ce logging set log-level DEBUG",
                ctx=ctx,
                param=param,
            ) from None

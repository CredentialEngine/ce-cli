from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table, box

from ce.config.context import CLIConfig, load_cli_config, save_cli_config
from ce.utils.output import OUTPUT_FORMATS

console = Console()
err_console = Console(stderr=True)


_SETTABLE_KEYS = {
    "output": "output_format",
}

_KEY_HELP = {
    "output": f"Default output format. One of: {', '.join(OUTPUT_FORMATS)}",
}


@click.group("config")
def config_group() -> None:
    """Manage CE CLI configuration."""


@click.command("set")
@click.argument("assignments", nargs=-1, required=True, metavar="KEY=VALUE...")
def config_set(assignments: tuple[str, ...]) -> None:
    """Set one or more CLI configuration values.

    \b
    Examples:
      ce config set output=json
      ce config set output=table
    """
    cli_config = load_cli_config()
    changed: list[str] = []
    errors: list[str] = []

    for assignment in assignments:
        if "=" not in assignment:
            errors.append(f"Invalid format '{assignment}' — expected KEY=VALUE.")
            continue

        key, _, value = assignment.partition("=")
        key = key.strip().lower()
        value = value.strip()

        if key not in _SETTABLE_KEYS:
            errors.append(
                f"Unknown key '{key}'. Valid keys: {', '.join(sorted(_SETTABLE_KEYS))}."
            )
            continue

        field = _SETTABLE_KEYS[key]

        # Validate
        if key == "output" and value not in OUTPUT_FORMATS:
            errors.append(
                f"Invalid value '{value}' for 'output'. "
                f"Must be one of: {', '.join(OUTPUT_FORMATS)}."
            )
            continue

        setattr(cli_config, field, value)
        changed.append(f"{key} = {value}")

    for err in errors:
        err_console.print(f"[red]✗[/red] {err}")

    if changed:
        save_cli_config(cli_config)
        for line in changed:
            console.print(f"[green]✓[/green] {line}")

    if errors:
        raise SystemExit(1)


# ce config get

@click.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Print the value of a configuration key.

    \b
    Example:
      ce config get output
    """
    key = key.strip().lower()
    cli_config = load_cli_config()

    if key not in _SETTABLE_KEYS:
        err_console.print(
            f"[red]✗[/red] Unknown key '{key}'. "
            f"Valid keys: {', '.join(sorted(_SETTABLE_KEYS))}."
        )
        raise SystemExit(1)

    field = _SETTABLE_KEYS[key]
    value = getattr(cli_config, field, None)
    click.echo(value if value is not None else "")


@click.command("list")
def config_list() -> None:
    """List all CLI configuration values."""
    cli_config = load_cli_config()

    table = Table(box=box.SIMPLE_HEAD, header_style="bold", border_style="dim")
    table.add_column("Key")
    table.add_column("Value")
    table.add_column("Description", style="dim")

    for key, field in sorted(_SETTABLE_KEYS.items()):
        value = getattr(cli_config, field, "")
        table.add_row(
            key,
            str(value) if value else "[dim]—[/dim]",
            _KEY_HELP.get(key, ""),
        )

    console.print()
    console.print(table)
    console.print()



@click.command("reset")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def config_reset(yes: bool) -> None:
    """Reset all CLI configuration to defaults.

    Environments and the active environment selection are preserved.
    """
    if not yes:
        click.confirm("  Reset all CLI configuration to defaults?", abort=True)

    current = load_cli_config()
    # Preserve environments and active env; only reset preferences.
    reset = CLIConfig(
        current_environment=current.current_environment,
        environments=current.environments,
    )
    save_cli_config(reset)
    console.print("[green]✓[/green] Configuration reset to defaults.")


config_group.add_command(config_set)
config_group.add_command(config_get)
config_group.add_command(config_list)
config_group.add_command(config_reset)
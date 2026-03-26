"""Environment command group: ce env list/add/use/show/remove."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box

from ce.config.context import (
    DEFAULT_ENVIRONMENTS,
    Environment,
    get_current_environment,
    load_cli_config,
    save_cli_config,
)

console = Console()
err_console = Console(stderr=True)


@click.group("env")
def env_group() -> None:
    """Manage Credential Engine environments (dev, sandbox, prod, …)."""



@click.command("list")
def env_list() -> None:
    """List all configured environments."""
    config = load_cli_config()

    table = Table(box=box.SIMPLE_HEAD, header_style="bold", border_style="dim")
    table.add_column("")
    table.add_column("Name")
    table.add_column("Label")
    table.add_column("Publisher base")

    for name, env in sorted(config.environments.items()):
        active = "[green]●[/green]" if name == config.current_environment else " "
        bold = name == config.current_environment
        table.add_row(
            active,
            f"[bold]{name}[/bold]" if bold else name,
            env.label,
            env.publisher_base,
        )

    console.print()
    console.print(table)
    if config.current_environment:
        console.print(f"  Active: [bold green]{config.current_environment}[/bold green]")
    console.print()



@click.command("add")
@click.argument("name")
@click.option("--label",          default=None, help="Human-readable label.")
@click.option("--client-id",      default=None, metavar="ID",  help="OIDC client ID.")
@click.option("--device-auth-url",default=None, metavar="URL", help="Device authorization endpoint.")
@click.option("--token-url",      default=None, metavar="URL", help="Token endpoint.")
@click.option("--scopes",         default=None, help="Space-separated OIDC scopes.")
@click.option("--publisher-base", default=None, metavar="URL", help="Publisher service base URL.")
@click.option("--no-ssl-verify",  is_flag=True, default=False, help="Disable SSL verification.")
@click.option("--activate", "-a", is_flag=True, default=False, help="Set as active immediately.")
def env_add(name, label, client_id, device_auth_url, token_url, scopes,
            publisher_base, no_ssl_verify, activate):
    config = load_cli_config()
    existing = name in config.environments
    base = DEFAULT_ENVIRONMENTS.get(name) or config.environments.get(name)

    if base is None and not all([label, client_id, device_auth_url, token_url, publisher_base]):
        err_console.print(
            f"[red]✗[/red] '{name}' is not a built-in environment. "
            "Provide all required options: --label, --client-id, --device-auth-url, "
            "--token-url, --publisher-base."
        )
        raise SystemExit(1)

    config.environments[name] = Environment(
        label=           label            or (base.label if base else name),
        client_id=       client_id        or (base.client_id if base else ""),
        device_auth_url= device_auth_url  or (base.device_auth_url if base else ""),
        token_url=       token_url        or (base.token_url if base else ""),
        scopes=          scopes           or (base.scopes if base else "openid profile"),
        publisher_base=  publisher_base   or (base.publisher_base if base else ""),
        ssl_verify=      not no_ssl_verify,
    )
    if activate or config.current_environment is None:
        config.current_environment = name

    save_cli_config(config)
    verb = "Updated" if existing else "Added"
    console.print(f"[green]✓[/green] {verb} environment [bold]{name}[/bold]")
    if config.current_environment == name:
        console.print("  [dim]Now active.[/dim]")


@click.command("use")
@click.argument("name")
def env_use(name: str) -> None:
    """Set NAME as the active environment."""
    config = load_cli_config()
    if name not in config.environments:
        err_console.print(
            f"[red]✗[/red] Unknown environment [bold]{name}[/bold]. "
            "Run [bold]ce env list[/bold] to see available environments."
        )
        raise SystemExit(1)
    config.current_environment = name
    save_cli_config(config)
    env = config.environments[name]
    console.print(f"[green]✓[/green] Switched to [bold]{name}[/bold] ({env.label}).")


@click.command("show")
@click.argument("name", required=False)
def env_show(name: str | None) -> None:
    """Show all details for an environment (defaults to active)."""
    config = load_cli_config()
    target = name or config.current_environment

    if not target:
        err_console.print("[yellow]⚠[/yellow]  No active environment.")
        return

    env = config.environments.get(target)
    if not env:
        err_console.print(f"[red]✗[/red] Environment [bold]{target}[/bold] not found.")
        raise SystemExit(1)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value", style="bold")

    active_label = " [green](active)[/green]" if target == config.current_environment else ""
    rows = [
        ("Name",             f"{target}{active_label}"),
        ("Label",            env.label),
        ("Client ID",        env.client_id),
        ("Device auth URL",  env.device_auth_url),
        ("Token URL",        env.token_url),
        ("Scopes",           env.scopes),
        ("Publisher base",   env.publisher_base),
        ("SSL verify",       str(env.ssl_verify)),
    ]
    for k, v in rows:
        table.add_row(k, v)

    console.print()
    console.print(Panel(table, title=f"[bold]Environment: {target}[/bold]",
                        border_style="blue", padding=(1, 2)))
    console.print()



@click.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def env_remove(name: str, yes: bool) -> None:
    """Remove environment NAME."""
    config = load_cli_config()
    if name not in config.environments:
        err_console.print(f"[red]✗[/red] Environment [bold]{name}[/bold] not found.")
        raise SystemExit(1)

    if not yes:
        click.confirm(f"  Remove environment '{name}'?", abort=True)

    del config.environments[name]
    if config.current_environment == name:
        config.current_environment = next(iter(config.environments), None)
        if config.current_environment:
            console.print(f"  [dim]Switched active environment to "
                          f"[bold]{config.current_environment}[/bold].[/dim]")

    save_cli_config(config)
    console.print(f"[green]✓[/green] Removed environment [bold]{name}[/bold].")


# ---------------------------------------------------------------------------
# Wire up
# ---------------------------------------------------------------------------

env_group.add_command(env_list,   name="list")
env_group.add_command(env_add,    name="add")
env_group.add_command(env_use,    name="use")
env_group.add_command(env_show,   name="show")
env_group.add_command(env_remove, name="remove")
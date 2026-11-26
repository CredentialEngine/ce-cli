"""Registry command registration."""

import click

from ce.commands.registry_downloads import downloads
from ce.commands.registry_resources import graphs, metadata, resources
from ce.registry.search import search_group


@click.group("registry")
@click.pass_context
def registry_group(ctx):
    """Search Credential Registry resources and manage exports."""
    ctx.ensure_object(dict)


registry_group.add_command(search_group)
registry_group.add_command(downloads)

registry_group.add_command(resources)
registry_group.add_command(graphs)
registry_group.add_command(metadata)

"""Independent Registry point lookup command groups."""

import click


def lookup(ctx, kind, identifier, **kwargs):
    from ce.registry.resources import execute_lookup

    execute_lookup(ctx, kind, identifier, **kwargs)


@click.group("resources")
def resources():
    """Retrieve individual Registry resources."""


@resources.command("get")
@click.argument("identifier")
@click.pass_context
def get_resource(ctx, identifier):
    """Retrieve a resource by CTID or blank-node GUID (JSON-LD)."""
    lookup(ctx, "resources", identifier)


@click.group("graphs")
def graphs():
    """Retrieve Registry resource graphs."""


@graphs.command("get")
@click.argument("identifier")
@click.option("--depth", type=click.IntRange(min=0), help="Graph traversal depth.")
@click.pass_context
def get_graph(ctx, identifier, depth):
    """Retrieve a graph by CTID."""
    lookup(ctx, "graphs", identifier, depth=depth)


@click.group("metadata")
def metadata():
    """Retrieve Registry resource metadata."""


@metadata.command("get")
@click.argument("identifier")
@click.pass_context
def get_metadata(ctx, identifier):
    """Retrieve metadata by CTID."""
    lookup(ctx, "metadata", identifier)

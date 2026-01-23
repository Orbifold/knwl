import asyncio
import json
from typing import Optional, Annotated
from knwl.knwl import Knwl
import typer
from knwl.config import get_config, resolve_config
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.padding import Padding
from rich.table import Table

console = Console()
# create a sub-app for config commands
graph_app = typer.Typer(help="Inspect and manipulate the knowledge graph.")


def _get(node, field):
    """Safely get field from a dict or model-like object."""
    if isinstance(node, dict):
        return node.get(field, "")
    return getattr(node, field, "")


@graph_app.command(
    "count",
    help="Count elements in the knowledge graph.",
    epilog="Example:\n  knwl graph count nodes",
)
def count(
    ctx: typer.Context,
    what: Optional[str] = typer.Argument(
        "nodes edges", help="What to count (e.g. 'edge' or 'nodes')"
    ),
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    knwl = ctx.obj  # type: Knwl
    answer = ""
    if "node" in what.lower():
        nodes = asyncio.run(knwl.node_count())
        answer += f"**Nodes**: {nodes}\n"
    if "edge" in what.lower():
        edges = asyncio.run(knwl.edge_count())
        answer += f"**Edges**: {edges}\n"
    if raw:
        j = {
            "nodes": nodes if "node" in what.lower() else None,
            "edges": edges if "edge" in what.lower() else None,
        }
        console.print(json.dumps(j, indent=2))
    else:
        console.print(
            Panel(Padding(Markdown(answer.strip()), (1, 2)), title="Count Results")
        )


@graph_app.command(
    "types",
    help="Inspect all types in the knowledge graph.",
    epilog="Example:\n  knwl graph types",
)
def show_types(
    ctx: typer.Context,
    what: Optional[str] = typer.Argument(
        None, help="What to inspect (e.g. 'nodes' or 'edges')"
    ),
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    if what is None:
        what = "nodes edges"
    what = what.strip().lower()
    if len(what) == 0:
        what = "nodes edges"
    json_output = {}
    if "node" in what:
        knwl = ctx.obj  # type: Knwl
        stats = asyncio.run(knwl.node_stats())
        if not raw:
            table = Table(title="Node Statistics")
            table.add_column("Node Type", style="cyan", no_wrap=True)
            table.add_column("Count", style="magenta")
            for node_type, count in sorted(stats.items()):
                table.add_row(node_type.upper(), str(count))
            console.print(Padding(table, (1, 2)))
        else:
            json_output["nodes"] = stats
    if "edge" in what:
        knwl = ctx.obj  # type: Knwl
        stats = asyncio.run(knwl.edge_stats())
        if not raw:
            table = Table(title="Edge Statistics")
            table.add_column("Edge Type", style="cyan", no_wrap=True)
            table.add_column("Count", style="magenta")
            for edge_type, count in sorted(stats.items()):
                table.add_row(edge_type.upper(), str(count))
            console.print(Padding(table, (1, 2)))
        else:
            json_output["edges"] = stats
    if raw:
        console.print(json.dumps(json_output, indent=2))


@graph_app.command(
    "stats",
    help="Show statistics of the knowledge graph.",
    epilog="Example:\n  knwl graph stats nodes",
)
def show_stats(
    ctx: typer.Context,
    what: Optional[str] = typer.Argument(
        None, help="What to inspect (e.g. 'nodes' or 'edges')"
    ),
):
    """
    Called in case no subcommand is given, ie. `knwl graph`.
    """
    show_types(ctx, what)


@graph_app.command(
    "type",
    help="Inspect one type in the knowledge graph.",
    epilog="Example:\n  knwl graph type Person",
)
def get_type(
    ctx: typer.Context,
    what: Optional[str] = typer.Argument(
        ..., help="What to inspect (e.g. 'types', 'stats', 'Person' or 'Location')"
    ),
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):

    knwl = ctx.obj  # type: Knwl
    nodes = asyncio.run(knwl.get_nodes_by_type(what))
    if raw:
        console.print(
            json.dumps(
                [node.dict() if hasattr(node, "dict") else node for node in nodes],
                indent=2,
            )
        )
        return
    if nodes is None or len(nodes) == 0:
        console.print(
            Panel(
                Padding(Markdown(f"No nodes found of type '**{what}**'."), (1, 2)),
                title="Node Inspection",
            )
        )
        return
    table = Table(title=f"Nodes of type '{what}'")

    table.add_column("Name", style="magenta")
    table.add_column("Description")
    for node in nodes:
        table.add_row(str(_get(node, "name")), str(_get(node, "description")))
    console.print(table)


@graph_app.command(
    "similar",
    help="Find similar nodes in the knowledge graph matching a query.",
    epilog="Example:\n  knwl graph similar 'George Washington'",
)
def similar_nodes(
    ctx: typer.Context,
    query: Annotated[
        str, typer.Argument(..., help="Search query to find nodes in the graph")
    ],
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    """Find nodes in the knowledge graph matching the query."""
    knwl = ctx.obj  # type: Knwl
    nodes_tuples = asyncio.run(knwl.similar_nodes(query))
    if raw:
        console.print(
            json.dumps(
                [
                    {
                        "node": node.dict() if hasattr(node, "dict") else node,
                        "distance": distance,
                    }
                    for node, distance in nodes_tuples
                ],
                indent=2,
            )
        )
        return
    if nodes_tuples is None or len(nodes_tuples) == 0:
        console.print(
            Panel(
                Padding(
                    Markdown(f"No nodes found matching query '**{query}**'."), (1, 2)
                ),
                title="Node Search",
            )
        )
        return
    table = Table(title=f"Nodes matching query '{query}'")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Distance", style="green")
    table.add_column("Description")
    for node, distance in nodes_tuples:
        table.add_row(
            str(_get(node, "type")),
            str(_get(node, "name")),
            f"{distance:.2f}",
            str(_get(node, "description")),
        )
    console.print(table)


@graph_app.command(
    "find",
    help="Find nodes in the knowledge graph by scanning the name and description of the nodes.",
    epilog="Example:\n  knwl graph find 'George Washington'",
)
def find_nodes(
    ctx: typer.Context,
    query: Annotated[
        str, typer.Argument(..., help="Search query to find nodes in the graph")
    ],
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    """Find nodes in the knowledge graph matching the query."""
    knwl = ctx.obj  # type: Knwl
    nodes = asyncio.run(knwl.find_nodes(query))
    if raw:
        console.print(
            json.dumps(
                [node.dict() if hasattr(node, "dict") else node for node in nodes],
                indent=2,
            )
        )
        return
    if nodes is None or len(nodes) == 0:
        console.print(
            Panel(
                Padding(
                    Markdown(f"No nodes found matching query '**{query}**'."), (1, 2)
                ),
                title="Node Search",
            )
        )
        return
    table = Table(title=f"Nodes matching query '{query}'")

    table.add_column("Type", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Description")
    for node in nodes:
        table.add_row(
            str(_get(node, "type")),
            str(_get(node, "name")),
            str(_get(node, "description")),
        )
    console.print(table)


@graph_app.command(
    "export",
    help="Export the knowledge graph in various formats.",
    epilog="Example:\n  knwl graph export --format json",
)
def export(
    ctx: typer.Context,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Export format (e.g. 'json', 'csv', 'xml')",
        ),
    ] = "json",
):
    """Export the knowledge graph in the specified format."""
    knwl = ctx.obj  # type: Knwl
    data = asyncio.run(knwl.export_graph(format=format))
    console.print(data)


@graph_app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):
    """
    Called in case no subcommand is given, ie. `knwl info`.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

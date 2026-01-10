import asyncio
from typing import Optional
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
):
    knwl = ctx.obj  # type: Knwl
    answer = ""
    if "node" in what.lower():
        nodes = asyncio.run(knwl.node_count())
        answer += f"**Nodes**: {nodes}\n"
    if "edge" in what.lower():
        edges = asyncio.run(knwl.edge_count())
        answer += f"**Edges**: {edges}\n"
    console.print(
        Panel(Padding(Markdown(answer.strip()), (1, 2)), title="Count Results")
    )


@graph_app.command(
    "types",
    help="Inspect all types in the knowledge graph.",
    epilog="Example:\n  knwl graph types",
)
def show_types(ctx: typer.Context, what: Optional[str] = typer.Argument(None, help="What to inspect (e.g. 'nodes' or 'edges')")):  
    if what is None:
        what = "nodes edges"
    what = what.strip().lower()
    if len(what) == 0:
        what = "nodes edges"
    if "node" in what:
        knwl = ctx.obj  # type: Knwl
        stats = asyncio.run(knwl.node_stats())
        table = Table(title="Node Statistics")
        table.add_column("Node Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="magenta")
        for node_type, count in sorted(stats.items()):
            table.add_row(node_type.upper(), str(count))
        console.print(Padding(table, (1, 2)))
    if "edge" in what:
        knwl = ctx.obj  # type: Knwl
        stats = asyncio.run(knwl.edge_stats())
        table = Table(title="Edge Statistics")
        table.add_column("Edge Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="magenta")
        for edge_type, count in sorted(stats.items()):
            table.add_row(edge_type.upper(), str(count))
        console.print(Padding(table, (1, 2)))

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
):
    
    knwl = ctx.obj  # type: Knwl
    nodes = asyncio.run(knwl.get_nodes_by_type(what))
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
        table.add_row(str(node.get("name", "")), str(node.get("description", "")))
    console.print(table)


@graph_app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):
    """
    Called in case no subcommand is given, ie. `knwl info`.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

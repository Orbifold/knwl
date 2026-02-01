import asyncio
import json
from typing_extensions import Annotated
import typer
from knwl.config import get_config, resolve_config
from rich.console import Console
from rich.panel import Panel
from rich.padding import Padding
from rich.markdown import Markdown
from rich.table import Table

from knwl.collect.wikipedia import WikipediaCollector
from knwl.format import print_knwl
from knwl.knwl import Knwl

console = Console()
chunk_app = typer.Typer(help="Utility to manage chunks.")


@chunk_app.command(
    "count",
    help="Returns the number of documents in the system.",
    epilog="Example:\n  knwl chunk count",
)
def get_chunk_count(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    knwl = ctx.obj  # type: Knwl
    count = asyncio.run(knwl.chunk_count())
    if count is not None:
        if raw:
            console.print(count)
        else:
            console.print(
                Panel(
                    Padding(Markdown(f"**Chunk Count**: {count}"), (1, 2)),
                    title="Chunk Count",
                )
            )
    else:
        console.print("No chunks found.")

@chunk_app.command(
    "ls",
    short_help="Lists chunks in the system.",
    help="Lists chunks in the system.",
    epilog="Example:\n  knwl chunk ls --amount 5",
)
@chunk_app.command(
    "list",
    short_help="Lists chunks in the system.",
    help="Lists chunks in the system.",
    epilog="Example:\n  knwl chunk list --amount 5",
)
def get_chunks(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
    amount: Annotated[
        int,
        typer.Option("--amount", "-a", help="Number of chunks to retrieve"),
    ] = 10,
):
    knwl = ctx.obj  # type: Knwl
    chunks = asyncio.run(knwl.get_all_chunks(amount=amount, include_content=False))
    if chunks is not None:
        if raw:
            console.print(json.dumps([chunk.model_dump() for chunk in chunks], indent=2))
        else:
            #    render a table of chunks
            table = Table(title="Chunks")
            table.add_column("Id", justify="right", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Description", style="green")
            for chunk in chunks:
                table.add_row(str(chunk.id), chunk.name, str(chunk.description))
            console.print(table)
    else:
        console.print("No chunks found.")
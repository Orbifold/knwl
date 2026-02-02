import asyncio
import json
import os
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
from knwl.models import KnwlDocument

console = Console()
blob_app = typer.Typer(help="Utility to manage blobs.")


@blob_app.command(
    "count",
    help="Returns the number of blobs in the system.",
    epilog="Example:\n  knwl blob count",
)
def get_blob_count(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    knwl = ctx.obj  # type: Knwl
    count = asyncio.run(knwl.blob_count())
    if count is not None:
        if raw:
            console.print(count)
        else:
            console.print(
                Panel(
                    Padding(Markdown(f"**Blob Count**: {count}"), (1, 2)),
                    title="Blob Count",
                )
            )
    else:
        console.print("No blobs found.")


@blob_app.command(
    "ls",
    short_help="Lists blobs in the system.",
    help="Lists blobs in the system.",
    epilog="Example:\n  knwl blob ls --amount 5",
)
@blob_app.command(
    "list",
    short_help="Lists blobs in the system.",
    help="Lists blobs in the system.",
    epilog="Example:\n  knwl blob list --amount 5",
)
def get_blobs(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
    amount: Annotated[
        int,
        typer.Option("--amount", "-a", help="Number of blobs to retrieve"),
    ] = 10,
):
    knwl = ctx.obj  # type: Knwl
    blobs = asyncio.run(knwl.get_all_blobs(amount=amount, include_data=False))
    if blobs is not None:
        if len(blobs) == 0:
            console.print("No blobs found.")
            return
        if raw:
            console.print(json.dumps([blob.model_dump() for blob in blobs], indent=2))
        else:
            #    render a table of blobs
            table = Table(title="Blobs")
            table.add_column("Id", justify="right", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Description", style="green")
            for blob in blobs:
                table.add_row(str(blob.id), blob.name, str(blob.description))
            console.print(table)
    else:
        console.print("No blobs found.")


@blob_app.command(
    "upload",
    help="Uploads a file as a blob to the system.",
    epilog="Example:\n  knwl blob upload /path/to/file.txt",
)
def upsert_file(ctx: typer.Context, file_path: str) -> str:
    knwl = ctx.obj  # type: Knwl
    blob_id = asyncio.run(
        knwl.blob_upsert_file(
            path=file_path,
            metadata={"source": "cli-upload"},
        )
    )
    console.print(f"Uploaded blob with id: [bold green]{blob_id}[/]")
    return blob_id

@blob_app.command("delete", help="Deletes a blob by its Id.", epilog="Example:\n  knwl blob delete <blob_id>")
def delete_blob(ctx: typer.Context, blob_id: str) -> None:
    knwl = ctx.obj  # type: Knwl
    success = asyncio.run(knwl.blob_delete_by_id(blob_id))
    if success:
        console.print(f"Deleted blob with id: [bold green]{blob_id}[/]")
    else:
        console.print(f"No blob found with id: [bold red]{blob_id}[/]")
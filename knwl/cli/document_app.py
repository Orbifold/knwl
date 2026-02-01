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
document_app = typer.Typer(help="Utility to manage documents.")


@document_app.command(
    "count",
    help="Returns the number of documents in the system.",
    epilog="Example:\n  knwl document count",
)
def get_document_count(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    knwl = ctx.obj  # type: Knwl
    count = asyncio.run(knwl.document_count())
    if count is not None:
        if raw:
            console.print(count)
        else:
            console.print(
                Panel(
                    Padding(Markdown(f"**Document Count**: {count}"), (1, 2)),
                    title="Document Count",
                )
            )
    else:
        console.print("No documents found.")

@document_app.command(
    "ls",
    short_help="Lists documents in the system.",
    help="Lists documents in the system.",
    epilog="Example:\n  knwl document ls --amount 5",
)
@document_app.command(
    "list",
    short_help="Lists documents in the system.",
    help="Lists documents in the system.",
    epilog="Example:\n  knwl document list --amount 5",
)
def get_documents(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
    amount: Annotated[
        int,
        typer.Option("--amount", "-a", help="Number of documents to retrieve"),
    ] = 10,
):
    knwl = ctx.obj  # type: Knwl
    documents = asyncio.run(knwl.get_all_documents(amount=amount, include_content=False))
    if documents is not None:
        if raw:
            console.print(json.dumps([doc.model_dump() for doc in documents], indent=2))
        else:
            #    render a table of documents
            table = Table(title="Documents")
            table.add_column("Id", justify="right", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Description", style="green")
            for doc in documents:
                table.add_row(str(doc.id), doc.name, str(doc.description))
            console.print(table)
    else:
        console.print("No documents found.")

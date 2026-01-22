from typing import Annotated
from knwl.format import print_knwl
from knwl.knwl import Knwl
from knwl.models.KnwlInput import KnwlInput
import typer
import asyncio
import json
from knwl.cli.config_app import config_app
from knwl.cli.info_app import info_app
from knwl.cli.graph_app import graph_app

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.padding import Padding

console = Console()
app = typer.Typer()

K = Knwl()
app.add_typer(config_app, name="config", context_settings={"obj": K})
app.add_typer(info_app, name="info", context_settings={"obj": K})
app.add_typer(graph_app, name="graph", context_settings={"obj": K})


@app.command(
    "extract",
    help="Extracts a returns a knowledge graph from the given text without ingesting it into the database.",
    epilog="Example:\n  knwl extract 'John Field was an Irish composer.'",
)
def extract(
    text: Annotated[str, typer.Argument(..., help="Text to extract knowledge from")],
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    g = asyncio.run(K.extract(text))
    if raw:
        console.print(json.dumps(g.model_dump(), indent=2))
    else:
        print_knwl(g)


@app.command(
    "add",
    help="Ingests the given text into the database.",
    epilog="Example:\n  knwl add 'John Field was an Irish composer.'",
)
def add(
    text: Annotated[str, typer.Argument(..., help="Text to ingest into the database")],
) -> None:
    """Ingests the given text into the database."""
    g = asyncio.run(K.add(text))
    print_knwl(g)


@app.command("ingest", hidden=True)  # hidden=True keeps it out of help text
def ingest(
    text: Annotated[str, typer.Argument(..., help="Text to ingest into the database")],
) -> None:
    """Alias for 'add' command."""
    add(text)


@app.command(
    "ask",
    help="Asks a question to the knowledge base and returns the answer.",
    epilog="Example:\n  knwl ask 'Who was John Field?'",
)
def ask(
    question: Annotated[
        str, typer.Argument(..., help="Question to ask the knowledge base")
    ],
    strategy: Annotated[
        str, typer.Option("--strategy", "-s", help="Strategy to use")
    ] = "local",
    simple: Annotated[
        bool,
        typer.Option(
            "--simple",
            "-S",
            help="Don't use the knowledge graph, ask the LLM directly.",
        ),
    ] = False,
) -> None:
    """Asks a question to the knowledge base and returns the answer."""
    answer = asyncio.run(K.ask(question))
    if simple:
        answer = asyncio.run(K.simple_ask(question))
        title = "Direct LLM Answer"
    else:
        input = KnwlInput(text=question, strategy=strategy)
        answer = asyncio.run(K.ask(input))
        title = "Knowledge Base Answer"
    console.print(Panel(Padding(Markdown(answer.answer), (1, 2)), title=title))


@app.command(
    "simple",
    help="Asks a direct question to the LLM without augmentation, ie. without the knowledge graph.",
    epilog="Example:\n  knwl simple 'What is spacetime?'",
)
def simple(
    question: Annotated[
        str,
        typer.Argument(
            ...,
            help="A direct question to the LLM without augmentation, ie. without the knowledge graph.",
        ),
    ],
) -> None:
    """Asks a question to the knowledge base and returns the answer as a string."""
    answer = asyncio.run(K.simple_ask(question))
    console.print(
        Panel(Padding(Markdown(answer.answer), (1, 2)), title="Direct LLM Answer")
    )


@app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):
    # Attach Knwl instance to the click context so sub-apps can access it via `ctx.obj`
    ctx.obj = K

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def main():
    """Entry point for console_scripts"""
    app()

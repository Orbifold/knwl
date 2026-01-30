import sys
from typing import Annotated, Optional
from knwl.format import print_knwl
from knwl.knwl import Knwl
from knwl.models.KnwlInput import KnwlInput
import typer
import asyncio
import json
from knwl.cli.config_app import config_app
from knwl.cli.info_app import info_app
from knwl.cli.log_app import log_app
from knwl.cli.collect_app import collect_app
from knwl.cli.graph_app import graph_app, similar_nodes, find_nodes

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.padding import Padding
from rich.spinner import Spinner

console = Console()
app = typer.Typer()

K = Knwl()
app.add_typer(config_app, name="config", context_settings={"obj": K})
app.add_typer(info_app, name="info", context_settings={"obj": K})
app.add_typer(log_app, name="log", context_settings={"obj": K})
app.add_typer(graph_app, name="graph", context_settings={"obj": K})
app.add_typer(collect_app, name="collect", context_settings={"obj": K})


def try_get_text(obj: Optional[str]) -> str:
    if obj is None:
        data = sys.stdin.read().strip()
    else:
        data = obj.strip()
    try:
        if "{" in data:
            j = json.loads(data.replace("\n", ""))
            if "type_name" in j:
                type_name = j["type_name"]
                if type_name == "KnwlInput" and "text" in j:
                    return j["text"]
                elif type_name == "KnwlDocument" and "content" in j:
                    return j["content"]
            else:
                if "text" in j:
                    return j["text"]
                elif "content" in j:
                    return j["content"]
        return data
    except json.JSONDecodeError as e:
        # console.print(f"Input is not valid JSON: {e}", style="bold yellow")
        return obj if obj is not None else ""


@app.command(
    "find",
    help="Find nodes in the knowledge graph matching a query.",
    epilog="Example:\n  knwl find 'George Washington'",
)
def find(
    ctx: typer.Context,
    text: Annotated[
        str, typer.Argument(..., help="Search text to find nodes in the graph")
    ],
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    return find_nodes(ctx=ctx, query=text, raw=raw)


@app.command(
    "similar",
    help="Find similar nodes in the knowledge graph matching a query.",
    epilog="Example:\n  knwl similar 'George Washington'",
)
def similar(
    ctx: typer.Context,
    text: Annotated[
        str, typer.Argument(..., help="Search text to find nodes in the graph")
    ],
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    return similar_nodes(ctx=ctx, query=text, raw=raw)


@app.command(
    "extract",
    help="Extracts a returns a knowledge graph from the given text without ingesting it into the database.",
    epilog="Example:\n  knwl extract 'John Field was an Irish composer.'",
)
def extract(
    obj: Annotated[
        Optional[str], typer.Argument(..., help="Text to extract knowledge from")
    ] = None,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    if obj is None:
        data = sys.stdin.read().strip()
    else:
        data = obj.strip()
    if not data:
        console.print("No input text provided for extraction.", style="bold red")
        return
    # if passed via pipe, data is a string
    with console.status("Extracting...\n", spinner="dots"):
        g = asyncio.run(K.extract(data))
        if raw:
            console.print(json.dumps(g.model_dump(), indent=2))
        else:
            print_knwl(g)


@app.command("inspect", hidden=True)  # hidden=True keeps it out of help text
def inspect(
    obj: Annotated[Optional[str], typer.Argument(...)] = None,
) -> None:
    """A simple command to inspect the text/content passed via pipes."""
    found = try_get_text(obj)
    if found is None:
        console.print(
            "Could not extract text or content from the provided input.",
            style="bold red",
        )
    else:
        console.print(f"[blue]Extracted text/content:[/]\n\n{found}")


@app.command(
    "add",
    help="Ingests the given text into the database.",
    epilog="Example:\n  knwl add 'John Field was an Irish composer.'",
)
def add(
    text: Annotated[
        Optional[str], typer.Argument(..., help="Text to ingest into the database")
    ] = None,
) -> None:
    """Ingests the given text into the database."""
    with console.status("Ingesting...\n", spinner="dots"):
        g = asyncio.run(K.add(text))
        print("")
        print_knwl(g)


@app.command("ingest", hidden=True)  # hidden=True keeps it out of help text
def ingest(
    obj: Annotated[
        Optional[str], typer.Argument(..., help="Text to ingest into the database")
    ] = None,
) -> None:
    """Alias for 'add' command."""
    found = try_get_text(obj)
    if found is None:
        console.print(
            "Could not extract text or content from the provided input.",
            style="bold red",
        )
    else:
        add(found)


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
def simple_ask(
    obj: Annotated[
        Optional[str],
        typer.Argument(
            ...,
            help="A direct question to the LLM without augmentation, ie. without the knowledge graph.",
        ),
    ] = None,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    """Asks a question to the knowledge base and returns the answer as a string."""
    found = try_get_text(obj)
    if found is None:
        console.print(
            "Could not extract text or content from the provided input.",
            style="bold red",
        )
    else:
        answer = asyncio.run(K.simple_ask(found))
        if raw:
            console.print(json.dumps(answer.model_dump(), indent=2))
            return
        console.print(
            Panel(Padding(Markdown(answer.answer), (1, 2)), title="Direct LLM Answer")
        )


@app.command("direct", hidden=True)  # hidden=True keeps it out of help text
def direct_ask(
    obj: Annotated[
        Optional[str],
        typer.Argument(
            ...,
            help="A direct question to the LLM without augmentation, ie. without the knowledge graph.",
        ),
    ] = None,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
) -> None:
    """Alias for 'simple' command."""
    simple_ask(obj, raw=raw)


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

import click
from rich.console import Console
from rich.text import Text

from knwl.entities import fast_entity_extraction_from_text
from knwl.knwl import Knwl
from knwl.utils import get_info
import asyncio
C = Console()

state = {"knwl": None, "input": []}


@click.group()
def cli():
    """KNWL CLI tool"""
    pass


@cli.command()
def version():
    """Show the version of KNWL"""
    info = get_info()
    C.print(
        Text(
            f"KNWL version {info['version']}. {info['description']}", style="bold green"
        )
    )


@cli.command()
def info():
    """Show information about KNWL"""
    info = get_info()
    C.print(
        Text(
            f"KNWL version {info['version']}. {info['description']}", style="bold green"
        )
    )


@cli.command()
@click.option(
    "-n",
    "--no-storage",
    is_flag=True,
    default=True,
    help="Do not store the extracted info into a workspace.",
)
@click.argument("text", nargs=-1)
def extract(no_storage, text):
    """
    Extract information from the given input.
    This is the same as `knwl add` but it returns the gained information.
    """

    if no_storage:
        nodes = asyncio.run(fast_entity_extraction_from_text(" ".join(text)))
        
        C.print("Extracted entities:", style="bold green")
        for node in nodes:
            C.print(f" - [bold green]{node.name}[/bold green] [bold blue]{node.type.upper()}[/bold blue] {node.description}")
    else:
        C.print("Extracted information will be stored in the workspace.", style="bold green")

@cli.command()
def query():
    """Run a query against KNWL"""
    if len(state["input"]) == 0:
        C.print(
            "No knowledge provided yet, use 'knwl add' to add knowledge.",
            style="bold red",
        )
        return
    if not state["knwl"]:
        state["knwl"] = Knwl()


@cli.command()
@click.option(
    "-m", "--many", type=bool, default=False, help="Add multiple knowledge items."
)
@click.argument("text", nargs=-1)
def add(many, text):
    """Add knowledge to KNWL"""
    if many:
        while True:
            knowledge = click.prompt(
                "Enter knowledge to add (type 'escape' to finish)", type=str
            )
            if knowledge.lower() == "escape":
                break
            state["input"].append(knowledge)
    else:
        state["input"].append(" ".join(text))
    C.print(f"Added {len(state['input'])} knowledge items.", style="bold green")


@cli.command()
def what():
    """Show what KNWL knows"""
    if not state["input"]:
        C.print(
            "No knowledge added yet. Add knowledge via 'knwl add'", style="bold red"
        )
        return
    C.print("KNWL knows:", style="bold green")
    for item in state["input"]:
        C.print(f" - {item}", style="bold blue")


@cli.command()
@click.option("--input", type=click.Path(exists=True), help="Path to the input file")
@click.option("--output", type=click.Path(), help="Path to the output file")
@click.option("--verbose", is_flag=True, help="Enable verbose mode")
def process(input, output, verbose):
    """Process input and output files"""
    if verbose:
        C.print("Verbose mode enabled", style="bold yellow")
    if input:
        C.print(f"Input file: {input}", style="bold blue")
    if output:
        C.print(f"Output file: {output}", style="bold blue")


if __name__ == "__main__":
    cli()

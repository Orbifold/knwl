import asyncio
import json
from typing_extensions import Annotated
import typer
from knwl.config import get_config, resolve_config
from rich.console import Console
from rich.panel import Panel
from rich.padding import Padding
from rich.markdown import Markdown
from knwl.collect.wikipedia import WikipediaCollector
from knwl.format import print_knwl

console = Console()
collect_app = typer.Typer(help="Utility to collect data.")


@collect_app.command(
    "wiki",
    help="Fetch a random Wikipedia article from a specified category.",
    epilog="Example:\n  knwl collect wiki 'Machine Learning'",
)
def get_wikipedia_article(
    article_title: str,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):

    found = asyncio.run(WikipediaCollector.fetch_article(article_title))
    if found:
        if raw:
            console.print(json.dumps(found.model_dump(), indent=2))
        else:
            print_knwl(found)
    else:
        console.print(
            f"[bold red]Failed to fetch article:[/] [bold yellow]{article_title}[/]"
        )


@collect_app.command(
    "url",
    help="Fetch the content of a webpage given its URL.",
    epilog="Example:\n  knwl collect url 'https://knwl.ai'",
)
def get_url(
    url: str,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    from knwl.collect.webpage import WebpageCollector

    found = asyncio.run(WebpageCollector.fetch_page(url))
    if found:
        if raw:
            console.print(json.dumps(found.model_dump(), indent=2))
        else:
            print_knwl(found)
    else:
        console.print(f"[bold red]Failed to fetch URL:[/] [bold yellow]{url}[/]")

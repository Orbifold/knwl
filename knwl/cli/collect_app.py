import asyncio
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


@collect_app.command("wiki", help="Fetch a random Wikipedia article from a specified category.", epilog="Example:\n  knwl collect wiki 'Machine Learning'")
def get_wikipedia_article(article_title: str):

    found = asyncio.run(WikipediaCollector.fetch_article(article_title))
    if found:
       print_knwl(found)
    else:
        console.print(f"[bold red]Failed to fetch article:[/] [bold yellow]{article_title}[/]")
 
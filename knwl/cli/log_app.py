from typing_extensions import Annotated
import typer
from knwl.config import get_config, resolve_config
from rich.console import Console
from rich.panel import Panel
from rich.padding import Padding
from rich.markdown import Markdown
from knwl.logging import log
from rich.table import Table

console = Console()
# create a sub-app for config commands
log_app = typer.Typer(help="View Knwl log info.")


@log_app.command("list", help="List log items.", epilog="Example:\n  knwl log list")
def list_log(
    ctx: typer.Context,
    amount: Annotated[
        int,
        typer.Option("--amount", "-a", help="Number of log items to list"),
    ] = 10,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
    severity: Annotated[
        str,
        typer.Option("--severity", "-s", help="Filter log items by severity level"),
    ] = None,
):
    """List log items."""
    log_items = log.list_items(amount=amount, severity=severity)
    if not log_items:
        console.print("No log items found.")
        raise typer.Exit()
    if raw:
        console.print(log_items)
        return

    table = Table(title="Knwl Log Items")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Timestamp", style="green")
    table.add_column("Severity", style="red")
    table.add_column("Message", style="white")

    for i, item in enumerate(log_items, start=1):
        u = item.split(" - ")
        timestamp, name, severity, message = u
        table.add_row(str(i), timestamp, severity, message)

    console.print(table)

@log_app.command("clear", help="Clear log items.", epilog="Example:\n  knwl log clear")
def clear_log():    
    """Clear log items."""
    log.clear_log()
    console.print("Log cleared.")


@log_app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):
    """
    Called in case no subcommand is given, ie. `knwl info`.
    """
    if ctx.invoked_subcommand is None:
        # this will use the __repr__ method of Knwl
        list_log(ctx)
        raise typer.Exit()

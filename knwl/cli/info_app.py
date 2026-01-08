import typer
from knwl.config import get_config, resolve_config
from rich.console import Console

console = Console()
# create a sub-app for config commands
info_app = typer.Typer(help="View info about Knwl installation.")


@info_app.command()
def version():
    """Show the version of knwl."""
    from knwl.cli.cli_utils import get_version

    console.print(f"[bold blue]Knwl version:[/] [bold yellow]{get_version()}[/]")


@info_app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):
    """
    Called in case no subcommand is given, ie. `knwl info`.
    """
    if ctx.invoked_subcommand is None:
        version()
        raise typer.Exit()
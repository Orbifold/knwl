import typer

from knwl.cli.config_app import config_app
from knwl.cli.info_app import info_app


app = typer.Typer()

app.add_typer(config_app, name="config")
app.add_typer(info_app, name="info")

@app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def main():
    """Entry point for console_scripts"""
    app()

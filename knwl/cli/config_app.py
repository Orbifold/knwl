import typer
from knwl.config import get_config, resolve_config
from rich.console import Console
console = Console()
# create a sub-app for config commands
config_app = typer.Typer(help="View or modify knwl configuration")


@config_app.command("get")
def get(
    keys: list[str] = typer.Argument(
        None, help="Config key path (e.g. 'llm.model' or 'llm model')"
    ),
    default: str = typer.Option(
        None, "-d", "--default", help="Default value if key not found"
    )
):
    """
    Get a configuration value.
    Accepts either a dotted single argument ("llm.model") or multiple keys ("llm model").
    """
    # keys might be None if no argument given
    # Typer will produce an empty list for missing varargs; handle that
    if not keys:
        value = get_config()
    else:
        # support both "llm.model" and "llm model"
        if len(keys) == 1 and "." in keys[0]:
            parsed_keys = keys[0].split(".")
        else:
            parsed_keys = list(keys)

        value = resolve_config(*parsed_keys)
    if value is None and default is not None:
        value = default
    if value is None:
        console.print(f"[red]Config key not found.[/]")
    else:

        if isinstance(value, (dict, list)):
            console.print_json(data=value)
        else:
            console.print(value)


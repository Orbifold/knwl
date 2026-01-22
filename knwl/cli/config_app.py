import json
from typing_extensions import Annotated
from knwl.knwl import Knwl
import typer
from knwl.config import get_config, resolve_config, set_config_value
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.padding import Padding
from rich.tree import Tree
from rich.pretty import Pretty
import re
from rich.text import Text

console = Console()
# create a sub-app for config commands
config_app = typer.Typer(help="View or modify knwl configuration")


@config_app.command(
    "reset",
    help="Reset the active configuration to the default configuration.",
    epilog="Example:\n  knwl config reset",
)
def reset_config():
    """
    Resets the active configuration to the default configuration.
    """
    from knwl.config import reset_active_config

    reset_active_config(save=True)
    console.print("[green]Configuration reset to default and saved.[/]")


@config_app.command("set",
    help="Set a configuration value.",
    epilog="Example:\n  knwl config set 'llm.ollama.model' 'custom_model:1b'",
)
def set_config(
    ctx: typer.Context,
    keys: list[str] = typer.Argument(
        None, help="Config key path (e.g. 'llm.ollama.model' or 'llm ollama model')"
    ),
    value: str = typer.Argument(
        ..., help="Value to set the configuration key to"
    ),
):
    """
    Sets a configuration value.
    Accepts either a dotted single argument ("llm.model") or multiple keys ("llm model").
    Note that this modifies the active configuration in memory only; to persist changes, use `knwl config save`.
    """
    knwl = ctx.obj  # type: Knwl
    # use the set_config_value function to set the value
    if not keys or not isinstance(keys, (list, tuple)):
        console.print("[red]No configuration keys provided.[/]")
        raise typer.Exit(code=1)
    # note that we save the config after setting
    set_config_value(value, *keys, save=True)
    console.print(f"[green]Configuration key '{'.'.join(keys)}' set to '{value}'.[/]")


@config_app.command("get")
def get(
    ctx: typer.Context,
    keys: list[str] = typer.Argument(
        None, help="Config key path (e.g. 'llm.ollama.model' or 'llm ollama model')"
    ),
    default: str = typer.Option(
        None, "-d", "--default", help="Default value if key not found"
    ),
):
    """
    Gets a resolved configuration value.
    Accepts either a dotted single argument ("llm.model") or multiple keys ("llm model"). Since it returns a resolved value you don't need to specify the variant.
    """
    # keys might be None if no argument given
    # Typer will produce an empty list for missing varargs; handle that
    knwl = ctx.obj  # type: Knwl
    # If keys is not a list/tuple (e.g. the default ArgumentInfo), treat as no keys
    if not keys or not isinstance(keys, (list, tuple)):
        value = get_config()
    elif keys[0] == "tree":
        return typer.echo(tree(ctx))
    elif keys[0] == "summary":
        return typer.echo(summary(ctx))
    elif keys[0] == "all":
        value = get_config()
    else:
        # support both "llm.model" and "llm model"
        if len(keys) == 1 and isinstance(keys[0], str):
            if "." in keys[0]:
                parsed_keys = keys[0].split(".")
            elif "/" in keys[0]:
                parsed_keys = keys[0].split("/")
            else:
                parsed_keys = keys[0].split(" ")
        else:
            parsed_keys = list(keys)
        value = get_config(*parsed_keys)

    if value is None and default is not None:
        value = default
    if value is None:
        console.print(f"[red]Config key not found.[/]")
    else:

        if isinstance(value, (dict, list)):
            console.print_json(data=value)
        else:
            console.print(value)


@config_app.command("tree")
def tree(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    """
    Show a summary of the current configuration as a tree.
    """
    knwl = ctx.obj  # type: Knwl
    config = knwl.config
    if raw:
        console.print(json.dumps(config, indent=2))
        return

    def _looks_like_markdown(s: str) -> bool:
        if not isinstance(s, str):
            return False
        # Heuristics: multiline content or common markdown constructs
        if "\n" in s:
            return bool(
                re.search(
                    r"(^#{1,6}\s)|(^\s*[-*+]\s)|(```)|(\[.*\]\(.*\))|(^>\s)", s, re.M
                )
            )
        # Single-line checks (links, emphasis, headings, code fences)
        return bool(
            re.search(
                r"(^#{1,6}\s)|(```)|(\[.*\]\(.*\))|(\*\*.*\*\*)|(\*.*\*)|(_.*_)", s
            )
        )

    def add_nodes(parent: Tree, key: str, val):
        if isinstance(val, dict):
            branch = parent.add(f"[bold magenta]{key}[/]")
            for k, v in val.items():
                add_nodes(branch, k, v)
        elif isinstance(val, list):
            branch = parent.add(f"[bold]{key}[/]")
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    sub = branch.add(f"[dim][{i}][/]")
                    for k, v in item.items():
                        add_nodes(sub, k, v)
                else:
                    if isinstance(item, str) and _looks_like_markdown(item):
                        branch.add(Markdown(item))
                    else:
                        branch.add(Pretty(item))
        else:
            if isinstance(val, str) and _looks_like_markdown(val):
                branch = parent.add(f"[bold]{key}[/]")
                branch.add(Markdown(val))
            else:
                parent.add(f"{key}: {val}")

    root = Tree("[bold blue]Knwl[/]")
    if isinstance(config, dict):
        for k, v in config.items():
            add_nodes(root, k, v)
    else:
        root.add(Pretty(config))

    console.print(Panel(Padding(root, (1, 2)), title="Configuration Tree"))


@config_app.command("summary")
def summary(
    ctx: typer.Context,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Return raw JSON rather than pretty print"),
    ] = False,
):
    """
    Show a summary of the current configuration.
    """
    knwl = ctx.obj  # type: Knwl
    config = knwl.config
    if raw:
        console.print(json.dumps(config, indent=2))
        return

    def print_summary(d, indent=0):
        for key, value in d.items():
            if isinstance(value, dict):
                class_name = ""
                if "class" in value:
                    class_path = value["class"]
                    class_name = f"[{class_path.split('.')[-1]}]"
                    del value["class"]
                description = value.get("description", "")
                if "description" in value:
                    del value["description"]
                # Render markdown descriptions using rich.Markdown, otherwise print inline
                if isinstance(description, str) and (
                    "\n" in description
                    or re.search(
                        r"(^#{1,6}\s)|(```)|(\[.*\]\(.*\))|(\*\*.*\*\*)|(\*.*\*)|(_.*_)",
                        description,
                        re.M,
                    )
                ):
                    console.print(" " * indent + f"[bold green]▪{key}[/] {class_name}")
                    console.print(Padding(Markdown(description), (1, 0, 1, indent + 1)))
                else:
                    console.print(
                        " " * indent
                        + f"[bold green]▪{key}[/] {class_name} {description}"
                    )
                print_summary(value, indent + 2)
            else:
                console.print(" " * indent + f"[bold]•{key}[/]: {value}")

    # Capture the summary output and render it inside a Panel with padding

    with console.capture() as capture:
        print_summary(config)
    captured = capture.get()
    console.print(
        Panel(Padding(Text.from_ansi(captured), (1, 2)), title="Configuration Summary")
    )


@config_app.command(
    "all",
    help="Get the entire configuration. Same as `knwl config get all`",
    epilog="Example:\n  knwl config all",
)
def all(ctx: typer.Context):
    """
    Get the entire configuration.
    """
    knwl = ctx.obj  # type: Knwl
    get(ctx, keys=["all"])


@config_app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context):
    """
    Called in case no subcommand is given, ie. `knwl config`.
    """
    if ctx.invoked_subcommand is None:
        summary(ctx)
        raise typer.Exit()

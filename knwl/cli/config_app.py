from knwl.knwl import Knwl
import typer
from knwl.config import get_config, resolve_config
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


@config_app.command("get")
def get(
    ctx: typer.Context,
    keys: list[str] = typer.Argument(
        None, help="Config key path (e.g. 'llm.model' or 'llm model')"
    ),
    default: str = typer.Option(
        None, "-d", "--default", help="Default value if key not found"
    ),
):
    """
    Get a configuration value.
    Accepts either a dotted single argument ("llm.model") or multiple keys ("llm model").
    """
    # keys might be None if no argument given
    # Typer will produce an empty list for missing varargs; handle that
    if not keys:
        knwl = ctx.obj  # type: Knwl
        value = knwl.config
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


@config_app.command("tree")
def tree(ctx: typer.Context):
    """
    Show a summary of the current configuration as a tree.
    """
    knwl = ctx.obj  # type: Knwl
    config = knwl.config

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
def summary(ctx: typer.Context):
    """
    Show a summary of the current configuration.
    """
    knwl = ctx.obj  # type: Knwl
    config = knwl.config

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
    console.print(Panel(Padding(Text.from_ansi(captured), (1, 2)), title="Configuration Summary"))

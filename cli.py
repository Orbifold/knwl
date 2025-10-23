"""
Knwl Chat Application - Interactive command-line interface for querying the knowledge graph.
"""
import asyncio

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from knwl import services

# Initialize Typer app and Rich console
app = typer.Typer(name="knwl-chat", help="Interactive chat interface for querying Knwl knowledge graph", add_completion=False, )
console = Console()
llm = None


def get_llm():
    global llm
    if llm is None:
        console.print("[cyan]Initializing Knwl...[/cyan]")
        llm = services.get_service("llm")
        console.print("[green]✓ Knwl initialized![/green]\n")
    return llm


def print_welcome():
    """Display welcome message."""
    welcome_text = """
# 🧠 Knwl Chat

Welcome to the Knwl interactive chat interface!

**Available commands:**
- Type your question to query the knowledge graph
- `/mode <local|global|naive|hybrid>` - Change query mode (default: local)
- `/help` - Show help information
- `/exit` or `/quit` - Exit the chat
- `Ctrl+C` - Exit the chat

**Query modes:**
- **local**: Searches node neighborhoods using keywords
- **global**: Searches edge relationships
- **naive**: Direct chunk retrieval without graph
- **hybrid**: Combines local and global strategies
    """
    console.print(Panel(Markdown(welcome_text), border_style="cyan"))


def print_help():
    """Display help information."""
    help_text = """
## Commands

- `/mode <mode>` - Switch between query modes:
  - `local` - Node-based neighborhood search (default)
  - `global` - Edge-based relationship search
  - `naive` - Simple chunk retrieval
  - `hybrid` - Combined local + global search
- `/help` - Show this help message
- `/exit` or `/quit` - Exit the application

## Tips

- Ask questions naturally about topics in your knowledge graph
- Use different modes to explore various aspects of the data
- The system will provide context and references with each answer
    """
    console.print(Panel(Markdown(help_text), border_style="blue"))


async def process_query(query: str, mode: str) -> None:
    """Process a user query and display the response."""
    llm = get_llm()
    a = await llm.ask(query)
    console.print(f"\n[bold green]{str(a.answer)}[/bold green]")


@app.command()
def chat(mode: str = typer.Option("local", "--mode", "-m", help="Query mode: local, global, naive, or hybrid"), ):
    """
    Start an interactive chat session with the Knwl knowledge graph.

    The chat interface allows you to query your knowledge graph using natural language
    and switch between different query strategies on the fly.
    """
    # Validate mode
    valid_modes = ["local", "global", "naive", "hybrid"]
    if mode not in valid_modes:
        console.print(f"[red]Invalid mode: {mode}[/red]")
        console.print(f"Valid modes: {', '.join(valid_modes)}")
        raise typer.Exit(1)

    current_mode = mode
    print_welcome()

    # Main chat loop
    try:
        while True:
            # Get user input
            user_input = Prompt.ask(f"\n[bold cyan]You[/bold cyan] ({current_mode})", default="").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()

                if cmd in ["/exit", "/quit"]:
                    console.print("\n[cyan]👋 Goodbye![/cyan]")
                    break

                elif cmd == "/help":
                    print_help()
                    continue

                elif cmd == "/mode":
                    if len(cmd_parts) < 2:
                        console.print(f"[yellow]Current mode: {current_mode}[/yellow]")
                        console.print(f"[yellow]Available modes: {', '.join(valid_modes)}[/yellow]")
                    else:
                        new_mode = cmd_parts[1].strip().lower()
                        if new_mode in valid_modes:
                            current_mode = new_mode
                            console.print(f"[green]✓ Switched to {current_mode} mode[/green]")
                        else:
                            console.print(f"[red]Invalid mode: {new_mode}[/red]")
                            console.print(f"[yellow]Available modes: {', '.join(valid_modes)}[/yellow]")
                    continue

                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
                    console.print("[yellow]Type /help for available commands[/yellow]")
                    continue

            # Process the query
            asyncio.run(process_query(user_input, current_mode))

    except KeyboardInterrupt:
        console.print("\n\n[cyan]👋 Goodbye![/cyan]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def query(question: str = typer.Argument(..., help="The question to query"), mode: str = typer.Option("local", "--mode", "-m", help="Query mode: local, global, naive, or hybrid"), ):
    """
    Execute a single query against the knowledge graph.

    This is useful for scripting or one-off queries without entering interactive mode.

    Example:
        knwl-chat query "What is machine learning?" --mode local
    """
    valid_modes = ["local", "global", "naive", "hybrid"]
    if mode not in valid_modes:
        console.print(f"[red]Invalid mode: {mode}[/red]")
        console.print(f"Valid modes: {', '.join(valid_modes)}")
        raise typer.Exit(1)

    # Process the query
    asyncio.run(process_query(question, mode))


@app.command()
def version():
    """Display the Knwl version."""
    console.print("[cyan]Knwl Chat v0.7.4[/cyan]")


if __name__ == "__main__":
    app()

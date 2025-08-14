from typing import Any

from rich import print as rich_print
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from knwl.models import KnwlResponse


def pretty_print(obj: Any, **kwargs) -> None:
    if isinstance(obj, KnwlResponse):
        print_response(obj, **kwargs)
    else:
        print(obj)


def print_response(response: KnwlResponse, chunks: bool = True, nodes: bool = True, edges: bool = True, references: bool = True, metadata: bool = True) -> None:
    """
    Print the response from the Knwl API in a pleasant format.
    """
    
    r = response
    rich_print("")
    rich_print(Panel(r.question, title="LOCAL", border_style="blue", expand=True, padding=(0, 1)))

    # ======================== Answer =====================================
    rich_print("")
    if len(r.answer) > 100:
        rich_print(Text(r.answer, style="bold green", overflow="fold", no_wrap=True))
    else:
        rich_print(Text(r.answer, style="bold green", no_wrap=True))
    # ======================== Chunks ====================================
    if chunks:
        rich_print("")
        table = Table(title="Chunks", min_width=500)
        table.add_column("Index", justify="right", style="cyan")
        table.add_column("Text", style="green", no_wrap=False)
        table.add_column("Order", justify="right")
        table.add_column("Id", justify="right")
        for c in r.context.chunks:
            table.add_row(str(c.index), c.text, str(c.order), c.id)
        rich_print(table)

    # ======================== Nodes =====================================
    if nodes:
        rich_print("")
        table = Table(title="Nodes", min_width=500)
        table.add_column("Id", justify="right", style="cyan")
        table.add_column("Name", justify="right", style="cyan")
        table.add_column("Type", justify="right", style="cyan")
        table.add_column("Description", justify="right", style="cyan")
        for n in r.context.nodes:
            table.add_row(n.id, n.name or "Not set", n.type or "Not set", n.description or "Not provided")
        rich_print(table)

    # ======================== Edges =====================================
    if edges:
        rich_print("")
        table = Table(title="Edges", min_width=500)
        table.add_column("Id", justify="right", style="cyan")
        table.add_column("Source", justify="right", style="cyan")
        table.add_column("Target", justify="right", style="cyan")
        table.add_column("Type", justify="right", style="cyan")
        table.add_column("Description", justify="right", style="cyan")
        for e in r.context.edges:
            table.add_row(e.id, e.source, e.target, ", ".join(e.keywords) or "Not set", e.description or "Not provided")
        rich_print(table)

    # ======================== References =====================================
    if references:
        rich_print("")
        table = Table(title="References", min_width=500)
        table.add_column("Id", justify="right", style="cyan", no_wrap=False)
        table.add_column("Name", justify="right", style="cyan", no_wrap=False)
        table.add_column("Description", justify="right", style="cyan", no_wrap=True)
        # table.add_column("Timestamp", justify="right", style="cyan", no_wrap=True)
        for r in r.context.references:
            table.add_row(r.id, r.name or "Not set", r.description or "Not provided")
        rich_print(table)

    # ======================== Metadata =====================================
    if metadata:
        rich_print("")
        table = Table(title="Metadata", min_width=500)
        table.add_column("Key", justify="right", style="cyan")
        table.add_column("Value", justify="left", style="cyan")
        table.add_row("Total time", f"{r.total_time}s")
        table.add_row("LLM time", f"{r.llm_time}s")
        table.add_row("RAG time", f"{r.rag_time}s")
        table.add_row("LLM Service", "Ollama")
        table.add_row("LLM Model", "Qwen2.5:4b")
        rich_print(table)

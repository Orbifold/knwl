from typing import Any

from httpx import options
from matplotlib.pyplot import table
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.console import Group

from knwl.format.formatter_base import ModelFormatter, register_formatter
from knwl.format.terminal.model_formatters import KnwlEdgeTerminalFormatter, KnwlNodeTerminalFormatter
from knwl.semantic.graph.semantic_graph import SemanticGraph


@register_formatter(SemanticGraph, "terminal")
class KnwlKeywordsTerminalFormatter(ModelFormatter):
    """Formatter for SemanticGraph service."""

    def format(self, service: SemanticGraph, formatter, **options) -> Panel:
        """Format a SemanticGraph as a rich panel."""
        show_nodes = options.get("show_nodes", True)
        show_edges = options.get("show_edges", True)
        max_items = options.get("max_items", 10)
        graph = service.graph_store
        content = [
            Text(f"Id: {graph.id}", style=formatter.theme.MUTED),
            Text(
                f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}",
                style=formatter.theme.MUTED,
            ),
        ]

        if graph.keywords:
            if len(graph.keywords) == 0:
                keywords = "None"
            elif len(graph.keywords) == 1:
                keywords = graph.keywords[0]
            else:
                keywords = ", ".join(graph.keywords[:2]) + (
                    "..." if len(graph.keywords) > 2 else ""
                )
            content.append(Text(f"Keywords: {keywords}", style=formatter.theme.MUTED))

        # Add nodes preview
        if show_nodes and graph.nodes:
            content.append(Text("\n"))
            content.append(Text("Nodes:", style=formatter.theme.SUBTITLE_STYLE))
            nodes_to_show = graph.nodes[:max_items]
            for node in nodes_to_show:
                node_formatter = KnwlNodeTerminalFormatter()
                content.append(node_formatter.format(node, formatter, compact=True))
            if len(graph.nodes) > max_items:
                content.append(
                    Text(
                        f"... and {len(graph.nodes) - max_items} more",
                        style=formatter.theme.MUTED,
                    )
                )

        # Add edges preview
        if show_edges and graph.edges:
            content.append(Text("\n"))
            content.append(Text("Edges:", style=formatter.theme.SUBTITLE_STYLE))
            edges_to_show = graph.edges[:max_items]
            for edge in edges_to_show:
                edge_formatter = KnwlEdgeTerminalFormatter()
                content.append(edge_formatter.format(edge, formatter, compact=True))
            if len(graph.edges) > max_items:
                content.append(
                    Text(
                        f"... and {len(graph.edges) - max_items} more",
                        style=formatter.theme.MUTED,
                    )
                )

        return formatter.create_panel(
            Group(*content),
            title="👁️ Semantic Graph",
            subtitle=f"{len(graph.nodes)} nodes, {len(graph.edges)} edges",
        )

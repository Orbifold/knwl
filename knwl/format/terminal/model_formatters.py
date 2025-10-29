"""
Model-specific formatters for terminal output using Rich.

This module contains formatters for all Knwl Pydantic models,
providing beautiful, informative terminal representations.
"""

from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from knwl.format.formatter_base import ModelFormatter, register_formatter
from knwl.models import (
    KnwlNode,
    KnwlEdge,
    KnwlGraph,
    KnwlDocument,
    KnwlChunk,
    KnwlEntity,
    KnwlExtraction,
    KnwlContext,
    KnwlResponse,
    KnwlIngestion,
    KnwlKeywords,
)


@register_formatter(KnwlNode, "terminal")
class KnwlNodeTerminalFormatter(ModelFormatter):
    """Formatter for KnwlNode models."""

    def format(self, model: KnwlNode, formatter, **options) -> Panel:
        """Format a KnwlNode as a rich panel."""
        compact = options.get("compact", False)

        if compact:
            # Compact single-line representation
            text = Text()
            text.append(model.name, style="bold cyan")
            text.append(" : ", style="dim")
            text.append(model.type, style="italic green")
            if model.description:
                desc = (
                    model.description[:150] + "..."
                    if len(model.description) > 50
                    else model.description
                )
                text.append(f" - {desc}", style="dim")
            return text

        # Full representation
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Field", style=formatter.theme.KEY_STYLE, width=15)
        table.add_column("Value", style=formatter.theme.VALUE_STYLE)

        table.add_row("Name", f"[bold]{model.name}[/bold]")
        table.add_row(
            "Type",
            f"[italic {formatter.theme.TYPE_STYLE}]{model.type}[/italic {formatter.theme.TYPE_STYLE}]",
        )
        table.add_row(
            "ID", f"[{formatter.theme.ID_STYLE}]{model.id}[/{formatter.theme.ID_STYLE}]"
        )

        if model.description:
            table.add_row("Description", model.description)

        if model.chunk_ids:
            chunk_text = f"[{formatter.theme.MUTED}]{len(model.chunk_ids)} chunks[/{formatter.theme.MUTED}]"
            table.add_row("Chunks", chunk_text)

        return formatter.create_panel(
            table, title="🔵 Knowledge Node", subtitle=model.type
        )


@register_formatter(KnwlEdge, "terminal")
class KnwlEdgeTerminalFormatter(ModelFormatter):
    """Formatter for KnwlEdge models."""

    def format(self, model: KnwlEdge, formatter, **options) -> Any:
        """Format a KnwlEdge as a rich representation."""
        compact = options.get("compact", False)

        if compact:
            # Compact arrow representation
            text = Text()
            text.append(model.source_id[:8], style="cyan")
            text.append(f" ─[{model.type}]→ ", style="bold green")
            text.append(model.target_id[:8], style="cyan")

            return text

        # Full representation
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Field", style=formatter.theme.KEY_STYLE, width=15)
        table.add_column("Value", style=formatter.theme.VALUE_STYLE)

        # Create visual arrow
        arrow = Text()
        arrow.append(model.source_id[:12], style="cyan")
        arrow.append(f" ─[{model.type}]→ ", style="bold yellow")
        arrow.append(model.target_id[:12], style="cyan")

        table.add_row("Connection", arrow)
        # table.add_row(
        #     "Type",
        #     f"[italic {formatter.theme.TYPE_STYLE}]{model.type}[/italic {formatter.theme.TYPE_STYLE}]",
        # )
        table.add_row(
            "ID", f"[{formatter.theme.ID_STYLE}]{model.id}[/{formatter.theme.ID_STYLE}]"
        )

        if model.description:
            table.add_row("Description", model.description)

        if model.chunk_ids:
            chunk_text = f"[{formatter.theme.MUTED}]{len(model.chunk_ids)} chunks[/{formatter.theme.MUTED}]"
            table.add_row("Chunks", chunk_text)

        return formatter.create_panel(
            table, title="🔗 Knowledge Edge", subtitle=model.type
        )


@register_formatter(KnwlGraph, "terminal")
class KnwlGraphTerminalFormatter(ModelFormatter):
    """Formatter for KnwlGraph models."""

    def format(self, model: KnwlGraph, formatter, **options) -> Panel:
        """Format a KnwlGraph as a rich panel with statistics."""
        show_nodes = options.get("show_nodes", True)
        show_edges = options.get("show_edges", True)
        max_items = options.get("max_items", 10)

        content = [
            Text(f"Id: {model.id}", style=formatter.theme.MUTED),
            Text(
                f"Nodes: {len(model.nodes)}, Edges: {len(model.edges)}",
                style=formatter.theme.MUTED,
            ),
        ]

        if model.keywords:
            if len(model.keywords) == 0:
                keywords = "None"
            elif len(model.keywords) == 1:
                keywords = model.keywords[0]
            else:
                keywords = ", ".join(model.keywords[:2]) + (
                    "..." if len(model.keywords) > 2 else ""
                )
            content.append(Text(f"Keywords: {keywords}", style=formatter.theme.MUTED))

        # Add nodes preview
        if show_nodes and model.nodes:
            content.append(Text("\n"))
            content.append(Text("🔵 Nodes:", style=formatter.theme.SUBTITLE_STYLE))
            nodes_to_show = model.nodes[:max_items]
            for node in nodes_to_show:
                node_formatter = KnwlNodeTerminalFormatter()
                content.append(node_formatter.format(node, formatter, compact=True))
            if len(model.nodes) > max_items:
                content.append(
                    Text(
                        f"... and {len(model.nodes) - max_items} more",
                        style=formatter.theme.MUTED,
                    )
                )

        # Add edges preview
        if show_edges and model.edges:
            content.append(Text("\n"))
            content.append(Text("🔗 Edges:", style=formatter.theme.SUBTITLE_STYLE))
            edges_to_show = model.edges[:max_items]
            for edge in edges_to_show:
                edge_formatter = KnwlEdgeTerminalFormatter()
                content.append(edge_formatter.format(edge, formatter, compact=True))
            if len(model.edges) > max_items:
                content.append(
                    Text(
                        f"... and {len(model.edges) - max_items} more",
                        style=formatter.theme.MUTED,
                    )
                )

        return formatter.create_panel(
            Group(*content),
            title="👁️ Knowledge Graph",
            subtitle=f"{len(model.nodes)} nodes, {len(model.edges)} edges",
        )


@register_formatter(KnwlDocument, "terminal")
class KnwlDocumentTerminalFormatter(ModelFormatter):
    """Formatter for KnwlDocument models."""

    def format(self, model: KnwlDocument, formatter, **options) -> Panel:
        """Format a KnwlDocument as a rich panel."""
        show_content = options.get("show_content", True)
        max_content_length = options.get("max_content_length", 500)

        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Field", style=formatter.theme.KEY_STYLE, width=15)
        table.add_column("Value", style=formatter.theme.VALUE_STYLE)

        table.add_row(
            "ID", f"[{formatter.theme.ID_STYLE}]{model.id}[/{formatter.theme.ID_STYLE}]"
        )

        if hasattr(model, "title") and model.title:
            table.add_row("Title", f"[bold]{model.title}[/bold]")

        if hasattr(model, "source") and model.source:
            table.add_row("Source", model.source)

        if show_content and model.content:
            content = model.content
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            table.add_row("Content", f"[dim]{content}[/dim]")
        else:
            table.add_row("Content Length", f"{len(model.content)} characters")

        return formatter.create_panel(
            table, title="📄 Document", subtitle=getattr(model, "title", "Untitled")
        )


@register_formatter(KnwlChunk, "terminal")
class KnwlChunkTerminalFormatter(ModelFormatter):
    """Formatter for KnwlChunk models."""

    def format(self, model: KnwlChunk, formatter, **options) -> Any:
        """Format a KnwlChunk as a rich representation."""
        compact = options.get("compact", False)

        if compact:
            text = Text()
            text.append(f"Chunk {model.index}", style="bold cyan")
            text.append(f" ({len(model.content)} chars)", style="dim")
            return text

        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Field", style=formatter.theme.KEY_STYLE, width=15)
        table.add_column("Value", style=formatter.theme.VALUE_STYLE)

        table.add_row(
            "ID", f"[{formatter.theme.ID_STYLE}]{model.id}[/{formatter.theme.ID_STYLE}]"
        )
        table.add_row("Index", str(model.index))
        table.add_row(
            "Document ID",
            f"[{formatter.theme.ID_STYLE}]{model.document_id}[/{formatter.theme.ID_STYLE}]",
        )

        content_preview = (
            model.content[:350] + "..." if len(model.content) > 150 else model.content
        )
        table.add_row("Content", f"[dim]{content_preview}[/dim]")
        table.add_row("Length", f"{len(model.content)} characters")

        return formatter.create_panel(
            table, title="📝 Chunk", subtitle=f"Index {model.index}"
        )


@register_formatter(KnwlEntity, "terminal")
class KnwlEntityTerminalFormatter(ModelFormatter):
    """Formatter for KnwlEntity models."""

    def format(self, model: KnwlEntity, formatter, **options) -> Panel:
        """Format a KnwlEntity as a rich panel."""
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Field", style=formatter.theme.KEY_STYLE, width=15)
        table.add_column("Value", style=formatter.theme.VALUE_STYLE)

        table.add_row("Name", f"[bold]{model.name}[/bold]")
        table.add_row(
            "Type",
            f"[italic {formatter.theme.TYPE_STYLE}]{model.type}[/italic {formatter.theme.TYPE_STYLE}]",
        )

        if hasattr(model, "description") and model.description:
            table.add_row("Description", model.description)

        return formatter.create_panel(table, title="🏷️  Entity", subtitle=model.type)


@register_formatter(KnwlExtraction, "terminal")
class KnwlExtractionTerminalFormatter(ModelFormatter):
    """Formatter for KnwlExtraction models."""

    def format(self, model: KnwlExtraction, formatter, **options) -> Panel:
        """Format a KnwlExtraction as a rich panel."""
        show_entities = options.get("show_entities", True)
        max_entities = options.get("max_entities", 10)

        # Statistics
        total_nodes = sum(len(nodes) for nodes in model.nodes.values())

        stats_table = Table(show_header=False, box=None, padding=(0, 1))
        stats_table.add_column("Metric", style=formatter.theme.KEY_STYLE)
        stats_table.add_column("Value", style=formatter.theme.HIGHLIGHT)

        stats_table.add_row("Entity Types", str(len(model.nodes)))
        stats_table.add_row("Total Nodes", str(total_nodes))
        stats_table.add_row("Edges", str(len(model.edges)))
        if model.keywords:
            stats_table.add_row("Keywords", ", ".join(model.keywords[:5]))

        content = [stats_table]

        # Show entity breakdown
        if show_entities and model.nodes:
            content.append(Text("\n"))
            content.append(
                Text("Entities by Type:", style=formatter.theme.SUBTITLE_STYLE)
            )

            entity_table = Table(box=formatter.theme.TABLE_BOX)
            entity_table.add_column("Type", style=formatter.theme.TYPE_STYLE)
            entity_table.add_column(
                "Count", style=formatter.theme.HIGHLIGHT, justify="right"
            )
            entity_table.add_column("Name", style=formatter.theme.VALUE_STYLE)

            for entity_name, nodes in list(model.nodes.items())[:max_entities]:
                entity_table.add_row(
                    ", ".join([u.type for u in nodes]), str(len(nodes)), entity_name
                )

            content.append(entity_table)

        return formatter.create_panel(
            Group(*content),
            title="🔍 Extraction Results",
            subtitle=f"{total_nodes} entities, {len(model.edges)} relationships",
        )


@register_formatter(KnwlContext, "terminal")
class KnwlContextTerminalFormatter(ModelFormatter):
    """Formatter for KnwlContext models."""

    def format(self, ctx: KnwlContext, formatter, **options) -> Panel:
        """Format a KnwlContext as a rich panel."""
        show_nodes = options.get("show_nodes", True)
        show_edges = options.get("show_edges", False)
        show_texts = options.get("show_texts", False)
        max_entities = options.get("max_entities", 10)
        content = []
        content.append(Text("\n"))
        content.append(
            Text(f"💬 Question: {ctx.input.text}", style=formatter.theme.SUBTITLE_STYLE)
        )
        if show_texts:
            content.append(Text("\n"))
            content.append(Text("📑 Chunks:\n", style=formatter.theme.SUBTITLE_STYLE))

            for c in ctx.texts[:max_entities]:
                preview = c.text[:150] + "..." if len(c.text) > 150 else c.text
                content.append(Text(f"📄[{str(c.index)}] {preview}"))
                content.append(Text("\n"))

        if show_nodes:
            content.append(Text("\n"))
            content.append(Text("🔵 Nodes:", style=formatter.theme.SUBTITLE_STYLE))
            entity_table = Table(box=formatter.theme.TABLE_BOX)
            entity_table.add_column("Name", style=formatter.theme.TYPE_STYLE)
            entity_table.add_column(
                "Type", style=formatter.theme.HIGHLIGHT, justify="right"
            )
            entity_table.add_column("Description", style=formatter.theme.VALUE_STYLE)

            for n in ctx.nodes[:max_entities]:
                entity_table.add_row(n.name, n.type, n.description)

            content.append(entity_table)
            
        if show_edges:
            content.append(Text("\n"))
            content.append(Text("🔗 Edges:", style=formatter.theme.SUBTITLE_STYLE))
            edge_table = Table(box=formatter.theme.TABLE_BOX)
            edge_table.add_column("Type", style=formatter.theme.TYPE_STYLE)
            edge_table.add_column(
                "Source", style=formatter.theme.HIGHLIGHT, justify="right"
            )
            edge_table.add_column(
                "Target", style=formatter.theme.VALUE_STYLE, justify="right"
            )

            for e in ctx.edges[:max_entities]:
                edge_table.add_row(e.type, e.source_name, e.target_name)

            content.append(edge_table)


        return formatter.create_panel(
            Group(*content),
            title="🎯 Context",
            subtitle=f"{len(ctx.texts)} chunks, {len(ctx.nodes)} nodes, {len(ctx.edges)} edges",
            width=320,  # Set explicit width (adjust as needed)
            expand=True,  # Or use expand=True to fill available space
        )


@register_formatter(KnwlResponse, "terminal")
class KnwlResponseTerminalFormatter(ModelFormatter):
    """Formatter for KnwlResponse models."""

    def format(self, model: KnwlResponse, formatter, **options) -> Panel:
        """Format a KnwlResponse as a comprehensive rich panel."""
        show_context = options.get("show_context", True)
        show_metadata = options.get("show_metadata", True)

        content = []

        # Question
        content.append(Text("💬 Question:", style=formatter.theme.SUBTITLE_STYLE))
        content.append(Text(model.question, style="bold white"))
        content.append(Text("\n"))

        # Answer
        content.append(Text("Answer:", style=formatter.theme.SUBTITLE_STYLE))
        content.append(Text(model.answer, style=formatter.theme.VALUE_STYLE))

        # Metadata
        if show_metadata:
            content.append(Text("\n"))
            meta_table = Table(show_header=False, box=None, padding=(0, 1))
            meta_table.add_column("Metric", style=formatter.theme.KEY_STYLE)
            meta_table.add_column("Value", style=formatter.theme.HIGHLIGHT)

            meta_table.add_row("RAG Time", f"{model.rag_time:.2f}s")
            meta_table.add_row("LLM Time", f"{model.llm_time:.2f}s")
            meta_table.add_row("Total Time", f"{model.total_time:.2f}s")
            meta_table.add_row("Timestamp", model.timestamp)

            content.append(meta_table)

        # Context summary
        if show_context and model.context:
            content.append(Text("\n"))
            context_formatter = KnwlContextTerminalFormatter()
            content.append(context_formatter.format(model.context, formatter))

        return formatter.create_panel(
            Group(*content),
            title="💬 Response",
            subtitle=f"Completed in {model.total_time:.2f}s",
            border_style=formatter.theme.SUCCESS,
        )


@register_formatter(KnwlIngestion, "terminal")
class KnwlIngestionTerminalFormatter(ModelFormatter):
    """Formatter for KnwlIngestion models."""

    def format(self, model: KnwlIngestion, formatter, **options) -> Panel:
        show_entities = options.get("show_entities", True)
        show_edges = options.get("show_edges", True)

        max_entities = options.get("max_entities", 10)
        """Format a KnwlIngestion as a rich panel with statistics."""
        content = [
            Text(f"Document Id: {model.input.id}", style=formatter.theme.MUTED),
            Text(
                f"Nodes: {len(model.graph.nodes)}, Edges: {len(model.graph.edges)}",
                style=formatter.theme.MUTED,
            ),
        ]
        if show_entities:
            content.append(Text("\n"))
            content.append(Text("Entities:", style=formatter.theme.SUBTITLE_STYLE))

            entity_table = Table(box=formatter.theme.TABLE_BOX)
            entity_table.add_column("Type", style=formatter.theme.TYPE_STYLE)
            entity_table.add_column("Name", style=formatter.theme.VALUE_STYLE)
            for node in model.graph.nodes[:max_entities]:
                entity_table.add_row(node.type, node.name)

            content.append(entity_table)

        if show_edges:
            content.append(Text("\n"))
            content.append(Text("🔗 Edges:", style=formatter.theme.SUBTITLE_STYLE))

            edge_table = Table(box=formatter.theme.TABLE_BOX)
            edge_table.add_column("Type", style=formatter.theme.TYPE_STYLE)
            edge_table.add_column("Source", style=formatter.theme.VALUE_STYLE)
            edge_table.add_column("Target", style=formatter.theme.VALUE_STYLE)
            for edge in model.graph.edges[:max_entities]:
                source_node = model.graph.get_node_by_id(edge.source_id)
                target_node = model.graph.get_node_by_id(edge.target_id)
                if source_node and target_node:
                    edge_table.add_row(edge.type, source_node.name, target_node.name)

            content.append(edge_table)

        return formatter.create_panel(
            Group(*content),
            title="👁️ Graph Ingestion",
            subtitle=f"{len(model.graph.nodes)} nodes, {len(model.graph.edges)} edges",
        )


@register_formatter(KnwlKeywords, "terminal")
class KnwlKeywordsTerminalFormatter(ModelFormatter):
    """Formatter for KnwlKeywords models."""

    def format(self, model: KnwlKeywords, formatter, **options) -> Panel:
        """Format a KnwlKeywords as a rich panel."""
        content = []

        content.append(Text("\n"))
        content.append(
            Text("🔼 High-Level Keywords:", style=formatter.theme.SUBTITLE_STYLE)
        )
        if model.high_level is None or len(model.high_level) == 0:
            content.append(Text("None", style="bold white"))
        else:
            content.append(
                Text(", ".join(model.high_level) or "None", style="bold white")
            )
        content.append(Text("\n"))
        content.append(
            Text("🔽 Low-Level Keywords:", style=formatter.theme.SUBTITLE_STYLE)
        )
        if model.low_level is None or len(model.low_level) == 0:
            content.append(Text("None", style="bold white"))
        else:
            content.append(
                Text(", ".join(model.low_level) or "None", style="bold white")
            )

        return formatter.create_panel(
            Group(*content),
            title="🏷️ Keywords Extraction",
            subtitle="Extracted Keywords",
        )

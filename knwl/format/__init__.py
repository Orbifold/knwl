"""
Knwl Formatting System

A generic, extensible formatting framework for pretty-printing Knwl models
in multiple output formats (terminal, HTML, markdown, etc.).

Usage Examples:

    # Terminal output with Rich
    from knwl.format import print_knwl, format_knwl
    from knwl.models import KnwlNode

    node = KnwlNode(name="Example", type="Concept")

    # Print directly to terminal
    print_knwl(node)

    # Get formatted object (for further manipulation)
    formatted = format_knwl(node, format_type="terminal")

    # HTML output
    html = format_knwl(node, format_type="html")
    print(html)

    # Save to HTML file
    render_knwl(node, format_type="html", output_file="output.html", full_page=True)

    # Markdown output
    md = format_knwl(node, format_type="markdown")
    print(md)

    # Register custom formatter for a new model
    from knwl.format import register_formatter
    from knwl.format.formatter_base import ModelFormatter

    @register_formatter(MyCustomModel, "terminal")
    class MyCustomFormatter(ModelFormatter):
        def format(self, model, formatter, **options):
            # Custom formatting logic
            return formatter.create_panel(...)

Design:
    - Uniform look and feel across all models
    - Easily extensible for new Pydantic models
    - Support for multiple output formats (terminal/HTML/markdown)
    - Registration system for custom formatters
    - Rich library for beautiful terminal output
"""

import json
from typing import Any, Optional

from knwl.format.formatter_base import (
    FormatterBase,
    ModelFormatter,
    FormatterRegistry,
    register_formatter,
    register_default_formatter,
    get_registry,
)

# Import formatters to trigger registration
from knwl.format.terminal.rich_formatter import RichFormatter
from knwl.format.html_formatter import HTMLFormatter
from knwl.format.markdown_formatter import MarkdownFormatter

# Import model formatters to trigger registration
from knwl.format.terminal import model_formatters
from knwl.models import KnwlGraph

# Cache formatter instances
_formatter_cache = {}


def get_formatter(format_type: str = "terminal") -> FormatterBase:
    """
    Gets a formatter for the specified format type.

    Args:
        format_type: The output format ('terminal', 'html', 'markdown')

    Returns:
        Formatter instance

    Raises:
        ValueError: If format_type is not supported
    """
    # lazy load and cache formatter instances
    if format_type in _formatter_cache:
        return _formatter_cache[format_type]

    if format_type == "terminal":
        formatter = RichFormatter()
    elif format_type == "html":
        formatter = HTMLFormatter()
    elif format_type == "markdown":
        formatter = MarkdownFormatter()

    else:
        raise ValueError(
            f"Unsupported format type: {format_type}. "
            f"Supported types: terminal, html, markdown"
        )

    _formatter_cache[format_type] = formatter
    return formatter


def format_knwl(obj: Any, format_type: str = "terminal", **options) -> Any:
    """
    Format a Knwl object for display.

    Args:
        obj: The object to format (typically a Pydantic model)
        format_type: The output format ('terminal', 'html', 'markdown')
        **options: Format-specific options

    Returns:
        Formatted object (type depends on format_type)
        - terminal: Rich renderable object
        - html: HTML string
        - markdown: Markdown string

    Examples:
        ```
        from knwl.models import KnwlNode
        node = KnwlNode(name="AI", type="Concept")

        # Get Rich Panel for terminal
        panel = format_knwl(node, format_type="terminal")

        # Get HTML string
        html = format_knwl(node, format_type="html")

        # Get Markdown string
        md = format_knwl(node, format_type="markdown")
        ```
    """
    formatter = get_formatter(format_type)
    return formatter.format(obj, **options)


def render_knwl(obj: Any, format_type: str = "terminal", **options) -> None:
    """
    Render a Knwl object to the output medium.

    Args:
        obj: The object to render
        format_type: The output format ('terminal', 'html', 'markdown')
        **options: Rendering options
            - For terminal: standard Rich console options
            - For html/markdown: output_file (str) to save to file
            - For html: full_page (bool) to wrap in complete HTML document
            - For markdown: add_frontmatter (bool) to add YAML frontmatter

    Examples:
        ```
        from knwl.models import KnwlGraph
        graph = KnwlGraph(nodes=[...], edges=[...])

        # Print to terminal
        render_knwl(graph)

        # Save as HTML file
        render_knwl(graph, format_type="html",
                   output_file="graph.html", full_page=True)

        # Save as Markdown
        render_knwl(graph, format_type="markdown",
                   output_file="graph.md", add_frontmatter=True)
        ```
    """
    formatter = get_formatter(format_type)
    formatter.render(obj, **options)


def render_mermaid(obj: KnwlGraph, **options) -> None:
    """
    Render a KnwlGraph object as a Mermaid diagram.

    Args:
        obj: The KnwlGraph object to render
        **options: Additional rendering options
    """
    formatter = get_formatter("markdown")
    if not isinstance(formatter, MarkdownFormatter):
        raise ValueError("Mermaid rendering is only supported in markdown format.")
    formatter.render_mermaid(obj, **options)


def print_knwl(obj: Any, **options) -> None:
    """
    Print a Knwl object to the terminal with Rich formatting.

    This is a convenience function equivalent to:
        render_knwl(obj, format_type="terminal", **options)

    Args:
        obj: The object to print
        **options: Formatting options passed to the formatter

    Example:
        ```
        from knwl.models import KnwlNode, KnwlEdge
        # Print a node
        node = KnwlNode(name="Python", type="Language")
        print_knwl(node)

        # Print with custom options
        print_knwl(node, compact=True)

        # Print a list of edges
        edges = [KnwlEdge(...), KnwlEdge(...)]
        print_knwl(edges)
        ```
    """
    if obj is None:
        print("print_knwl of None")
        return
    elif isinstance(obj, str):
        # this allows to print config references like "print_knwl(@/llm)" to see the default LLM config
        if obj.strip().startswith("@/"):
            from knwl.config import resolve_config
            try:
                print(json.dumps(resolve_config(obj.strip()), indent=2))
            except Exception as e:
                print(f"Error resolving config: {e}")
        else:
            print(obj)
        return
    else:
        render_knwl(obj, format_type="terminal", **options)


# Convenience exports
__all__ = [
    # Main functions
    "format_knwl",
    "render_knwl",
    "print_knwl",
    "get_formatter",
    # Base classes for extensions
    "FormatterBase",
    "ModelFormatter",
    "FormatterRegistry",
    # Decorators
    "register_formatter",
    "register_default_formatter",
    # Registry access
    "get_registry",
    # Formatter classes
    "RichFormatter",
    "HTMLFormatter",
    "MarkdownFormatter",
]

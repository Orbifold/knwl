"""
Example usage of the Knwl formatting system.

This script demonstrates how to use the generic formatting mechanism
to pretty-print Knwl models in various output formats.
"""

from knwl.models import KnwlNode, KnwlEdge, KnwlGraph, KnwlDocument, KnwlChunk
from knwl.format import print_knwl, format_knwl, render_knwl


def example_basic_usage():
    """Basic usage examples for terminal output."""
    print("\n" + "="*70)
    print("BASIC USAGE - Terminal Output with Rich")
    print("="*70)
    
    # Create a simple node
    node = KnwlNode(
        name="Artificial Intelligence",
        type="Concept",
        description="The simulation of human intelligence by machines, especially computer systems."
    )
    
    print("\n--- Pretty Print Node ---")
    print_knwl(node)
    
    # Create an edge
    edge = KnwlEdge(
        source_id="node_123",
        target_id="node_456",
        type="RELATES_TO",
        description="AI relates to machine learning"
    )
    
    print("\n--- Pretty Print Edge ---")
    print_knwl(edge)
    
    # Create a compact representation
    print("\n--- Compact Node Display ---")
    print_knwl(node, compact=True)
    print_knwl(edge, compact=True)


def example_graph_output():
    """Example of formatting a complex graph."""
    print("\n" + "="*70)
    print("GRAPH OUTPUT")
    print("="*70)
    
    # Create nodes
    nodes = [
        KnwlNode(name="Python", type="Programming Language", 
                description="A high-level programming language"),
        KnwlNode(name="Machine Learning", type="Field",
                description="A subset of AI focused on learning from data"),
        KnwlNode(name="TensorFlow", type="Library",
                description="An open-source ML framework"),
        KnwlNode(name="Neural Networks", type="Technique",
                description="Computing systems inspired by biological neural networks"),
    ]
    
    # Create edges
    edges = [
        KnwlEdge(source_id=nodes[0].id, target_id=nodes[2].id,
                type="IMPLEMENTS", description="Python implements TensorFlow"),
        KnwlEdge(source_id=nodes[2].id, target_id=nodes[1].id,
                type="USED_FOR", description="TensorFlow is used for ML"),
        KnwlEdge(source_id=nodes[3].id, target_id=nodes[1].id,
                type="PART_OF", description="Neural Networks are part of ML"),
    ]
    
    # Create graph
    graph = KnwlGraph(
        nodes=nodes,
        edges=edges,
        keywords=["AI", "ML", "Deep Learning"]
    )
    
    print("\n--- Full Graph Display ---")
    print_knwl(graph)
    
    print("\n--- Graph Stats Only (no details) ---")
    print_knwl(graph, show_nodes=False, show_edges=False)


def example_html_output():
    """Example of HTML output."""
    print("\n" + "="*70)
    print("HTML OUTPUT")
    print("="*70)
    
    node = KnwlNode(
        name="Graph Database",
        type="Technology",
        description="A database designed to treat relationships as first-class citizens"
    )
    
    # Get HTML string
    html = format_knwl(node, format_type="html")
    print("\n--- HTML Output ---")
    print(html)
    
    # Save to file
    print("\n--- Saving to HTML file ---")
    render_knwl(
        node,
        format_type="html",
        output_file="/tmp/knwl_node.html",
        full_page=True,
        title="Knowledge Node Example"
    )
    print("✓ Saved to /tmp/knwl_node.html")


def example_markdown_output():
    """Example of Markdown output."""
    print("\n" + "="*70)
    print("MARKDOWN OUTPUT")
    print("="*70)
    
    document = KnwlDocument(
        id="doc_001",
        content="This is a sample document about knowledge graphs. "
                "Knowledge graphs represent information as nodes and edges.",
        title="Introduction to Knowledge Graphs",
        source="example.txt"
    )
    
    # Get Markdown string
    md = format_knwl(document, format_type="markdown")
    print("\n--- Markdown Output ---")
    print(md)
    
    # Save to file with frontmatter
    print("\n--- Saving to Markdown file ---")
    render_knwl(
        document,
        format_type="markdown",
        output_file="/tmp/knwl_document.md",
        add_frontmatter=True,
        title="Knowledge Graph Document"
    )
    print("✓ Saved to /tmp/knwl_document.md")


def example_list_formatting():
    """Example of formatting lists of models."""
    print("\n" + "="*70)
    print("LIST FORMATTING")
    print("="*70)
    
    # Create multiple chunks
    chunks = [
        KnwlChunk(
            id=f"chunk_{i}",
            index=i,
            document_id="doc_001",
            content=f"This is the content of chunk {i}. " * 10
        )
        for i in range(5)
    ]
    
    print("\n--- List of Chunks ---")
    print_knwl(chunks)


def example_custom_formatter():
    """Example of registering a custom formatter for a new model."""
    print("\n" + "="*70)
    print("CUSTOM FORMATTER REGISTRATION")
    print("="*70)
    
    from pydantic import BaseModel
    from knwl.format import register_formatter
    from knwl.format.formatter_base import ModelFormatter
    
    # Define a custom model
    class CustomModel(BaseModel):
        title: str
        value: int
        enabled: bool
    
    # Register a custom formatter
    @register_formatter(CustomModel, "terminal")
    class CustomModelFormatter(ModelFormatter):
        def format(self, model, formatter, **options):
            from rich.text import Text
            
            text = Text()
            text.append("⭐ ", style="yellow")
            text.append(model.title, style="bold cyan")
            text.append(f" = {model.value}", style="magenta")
            status = "✓" if model.enabled else "✗"
            text.append(f" [{status}]", style="green" if model.enabled else "red")
            
            return formatter.create_panel(
                text,
                title="Custom Model",
                border_style="yellow"
            )
    
    # Use the custom formatter
    custom_obj = CustomModel(title="My Custom Object", value=42, enabled=True)
    
    print("\n--- Custom Formatted Output ---")
    print_knwl(custom_obj)
    
    print("\n✓ Custom formatter successfully registered and used!")


def main():
    """Run all examples."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              KNWL FORMATTING SYSTEM - EXAMPLES                       ║
║                                                                      ║
║  Demonstrating the generic, extensible formatting mechanism         ║
║  for pretty-printing Knwl models with Rich, HTML, and Markdown      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        example_basic_usage()
        example_graph_output()
        example_list_formatting()
        example_html_output()
        example_markdown_output()
        example_custom_formatter()
        
        print("\n" + "="*70)
        print("✓ All examples completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

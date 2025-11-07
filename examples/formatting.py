# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %% 
# Demonstration of knwl formatting capabilities
from knwl import KnwlAnswer
from knwl.format import print_knwl
from faker import Faker
from knwl.models import KnwlNode, KnwlEdge, KnwlGraph, KnwlDocument, KnwlChunk
from knwl.format import print_knwl, format_knwl, render_knwl
from knwl.utils import get_full_path
# ============================================================================================
# %%
# The `print_knwl`` is specifically for terminal output but also works in Jupyter.
fake = Faker()
# llm = OllamaClient()
# print(f"{llm}")
# a = await llm.ask("What is classical music?")
# print_knwl(a)
coll = []
for i in range(30):
    coll.append(
        KnwlAnswer(
            question=fake.sentence(nb_words=50), answer=fake.sentence(nb_words=200)
        )
    )

print_knwl(coll)

# ============================================================================================
# %%
# Single model output

node = KnwlNode(
    name="Artificial Intelligence",
    type="Concept",
    description="The simulation of human intelligence by machines, especially computer systems."
)

print_knwl(node)

edge = KnwlEdge(
    source_id="node_123",
    target_id="node_456",
    type="RELATES_TO",
    description="AI relates to machine learning"
)

print_knwl(edge)

# in compact mode the model are shown as one-liners which can be reused in tables
print_knwl(node, compact=True)
print_knwl(edge, compact=True)
# ============================================================================================
# %%
# Graph output

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

edges = [
    KnwlEdge(source_id=nodes[0].id, target_id=nodes[2].id,
            type="IMPLEMENTS", description="Python implements TensorFlow"),
    KnwlEdge(source_id=nodes[2].id, target_id=nodes[1].id,
            type="USED_FOR", description="TensorFlow is used for ML"),
    KnwlEdge(source_id=nodes[3].id, target_id=nodes[1].id,
            type="PART_OF", description="Neural Networks are part of ML"),
]

graph = KnwlGraph(
    nodes=nodes,
    edges=edges,
    keywords=["AI", "ML", "Deep Learning"]
)
 
print_knwl(graph)
 
print_knwl(graph, show_nodes=False, show_edges=False)

# ============================================================================================
#%%
# Example of HTML output.
 
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
output_file = get_full_path("$/tests/knwl_node.html")
render_knwl(
    node,
    format_type="html",
    output_file=output_file,
    full_page=True,
    title="Knowledge Node Example"
)

print(f"✓ Saved to {output_file}")
# ============================================================================================
# %%
# Example of Markdown output.

document = KnwlDocument(
    id="doc_001",
    content="This is a sample document about knowledge graphs. "
            "Knowledge graphs represent information as nodes and edges.",
    title="Introduction to Knowledge Graphs",
    source="example.txt"
)

md = format_knwl(document, format_type="markdown")
print(md)

output_file = get_full_path("$/tests/knwl_document.md")
render_knwl(
    document,
    format_type="markdown",
    output_file=output_file,
    add_frontmatter=True,
    title="Knowledge Graph Document"
)

print(f"✓ Saved to {output_file}")

# ============================================================================================
# %%
# Example of formatting lists of models.

chunks = [
    KnwlChunk(
        id=f"chunk_{i}",
        index=i,
        document_id="doc_001",
        content=f"This is the content of chunk {i}. " * 10
    )
    for i in range(5)
]

print_knwl(chunks)

# ============================================================================================
# %%
# Example of registering a custom formatter for a new model.


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
        text.append(f" = {model.value}", style="bold white")
        status = "✓" if model.enabled else "✗"
        text.append(f" [{status}]", style="green" if model.enabled else "red")
        
        return formatter.create_panel(
            text,
            title="Custom Model",
            border_style="yellow"
        )

# Use the custom formatter
custom_obj = CustomModel(title="My Custom Object", value=42, enabled=True)
print_knwl(custom_obj)
custom_obj = CustomModel(title="Disable it is", value=47, enabled=False)
print_knwl(custom_obj)

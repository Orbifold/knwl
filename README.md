# KNWL

A lightweight, protocol-based Graph RAG Python package with semantic search, classic RAG, and advanced graph-based retrieval strategies.

## Features

- **Four Graph RAG Strategies**: Local, Global, Naive, and Hybrid query modes for flexible knowledge retrieval
- **Dependency Injection Framework**: Decorator-based DI system (`@service`, `@singleton_service`, `@inject_config`) for clean, configurable architecture
- **Extensively Tested**: Comprehensive test suite covering all components and strategies
- **No External Services Required**: Runs with lightweight local implementations (Ollama, NetworkX, JSON storage) out of the box
- **Protocol-Based & Extensible**: Override base classes and configure via JSON to customize LLMs, storage, chunking, extraction, and more
- **FastAPI Integration**: REST API with uvicorn server for production deployments
- **MCP Services**: Model Context Protocol support for tool integration
- **Semantic Search**: Vector-based similarity search for nodes, edges, and chunks
- **Classic RAG**: Traditional retrieval-augmented generation with chunk-based context

## Architecture

KNWL uses a hierarchical configuration system with service variants, allowing runtime component swapping without code changes. All components inherit from `FrameworkBase` and are wired through dependency injection.

Core services include:

- **LLM**: Ollama, OpenAI (configurable via `llm.default`)
- **Storage**: JSON, Chroma, NetworkX graph storage
- **Chunking**: Tiktoken-based text splitting
- **Extraction**: Graph and entity extraction with customizable prompts
- **Vector Search**: Semantic similarity for retrieval

## Graph RAG Strategies

KNWL implements four distinct retrieval strategies for different query patterns:

### Local Strategy

Focuses on entity-centric retrieval:

- Extracts **low-level keywords** from the query and matches against nodes (primary nodes)
- Retrieves the **relationship neighborhood** around these primary nodes
- Builds context from:
  - Primary node records (name, type, description)
  - Connected relationship records (source, target, type, description)
  - Text chunks associated with the primary nodes

**Use case**: Questions about specific entities or concepts and their immediate relationships.

### Global Strategy

Focuses on relationship-centric retrieval:

- Extracts **high-level keywords** from the query and matches against edges
- Retrieves the **node endpoints** of matching edges
- Builds context from:
  - Node endpoint records (entities connected by the relationships)
  - Edge records (source, target, type, description)
  - Text chunks associated with the edges

**Use case**: Questions about relationships, connections, or patterns between entities.

### Naive Strategy

Traditional RAG approach:

- Performs direct **semantic similarity search** on text chunks
- No graph structure utilized
- Builds context purely from retrieved chunks

**Use case**: Simple fact-finding or when graph structure isn't beneficial.

### Hybrid Strategy

Combines Local and Global strategies:

- Executes both local and global retrieval in parallel
- Merges and deduplicates the combined context
- Provides comprehensive coverage across entities, relationships, and chunks

**Use case**: Complex queries benefiting from both entity and relationship context.

## Quick Start

```python
from knwl import Knwl

# Initialize with default configuration
knwl = Knwl()

# Ingest documents and build knowledge graph
await knwl.insert("Your text content here...")

# Query with different strategies
result = await knwl.query("Your question?", mode="local")    # or "global", "naive", "hybrid"
print(result.answer)
```

## API Access

Run the FastAPI server:

```bash
# Development mode (auto-reload)
python api/main.py

# Production with uvicorn
uvicorn knwl.api.main:app --host 0.0.0.0 --port 9000 --workers 8
```

## Formatting & Rendering

KNWL provides sophisticated formatting utilities for beautiful output across multiple mediums: **terminal**, **HTML**, and **Markdown**. The formatting system is protocol-based and extensible, allowing custom formatters for any Pydantic model.

### Terminal Output with Rich

The Rich-based terminal formatter creates beautiful, colorful console output with tables, panels, and trees:

```python
from knwl.format import print_knwl, format_knwl
from knwl.models import KnwlNode, KnwlEdge, KnwlGraph

# Print models directly to terminal with beautiful formatting
node = KnwlNode(name="AI", type="Concept", description="Artificial Intelligence")
print_knwl(node)  # Renders as formatted panel with table

# Format collections
edges = [KnwlEdge(...), KnwlEdge(...)]
print_knwl(edges)  # Renders as organized table with syntax highlighting

# Get formatted object for further manipulation
formatted = format_knwl(node, format_type="terminal")
```

**Features:**
- Consistent color schemes and styling across all models
- Automatic table generation for model fields
- Syntax highlighting for code and JSON
- Tree views for hierarchical data
- Customizable themes via `RichTheme`

### HTML Output

Generate semantic HTML with CSS classes for web displays, documentation, and reports:

```python
from knwl.format import render_knwl, format_knwl

# Get HTML string
html = format_knwl(node, format_type="html")

# Save to file with full page structure
render_knwl(
    graph,
    format_type="html",
    output_file="output.html",
    full_page=True,
    title="Knowledge Graph"
)
```

**Features:**
- Semantic HTML5 with CSS classes (`knwl-panel`, `knwl-table`, etc.)
- Customizable class mappings
- Full page generation with proper HTML structure
- Responsive tables and layouts

### Markdown Output

Create GitHub-flavored Markdown for documentation and static sites:

```python
# Generate markdown
md = format_knwl(graph, format_type="markdown")

# Save with frontmatter
render_knwl(
    result,
    format_type="markdown",
    output_file="report.md",
    add_frontmatter=True,
    title="Query Results"
)
```

**Features:**
- GitHub-flavored Markdown tables
- Code blocks with syntax highlighting
- Frontmatter support for static site generators
- Hierarchical headings for nested structures

### Custom Formatters

Register custom formatters for your own models:

```python
from knwl.format import register_formatter
from knwl.format.formatter_base import ModelFormatter

@register_formatter(MyCustomModel, "terminal")
class MyCustomFormatter(ModelFormatter):
    def format(self, model, formatter, **options):
        # Access Rich formatter's theming
        table = formatter.create_table(title="My Custom Output")
        # Add custom formatting logic
        return formatter.create_panel(table, title=model.name)
```

All KNWL models (`KnwlNode`, `KnwlEdge`, `KnwlGraph`, `KnwlAnswer`, `KnwlContext`, etc.) have pre-registered formatters for consistent output across formats.

## Extensibility

Override base classes and update `knwl/config.py`:

```python
# Custom LLM implementation
class MyLLM(LLMBase):
    async def complete(self, prompt: str) -> str:
        # Your implementation
        pass

# Add to config
"llm": {
    "default": "my_llm",
    "my_llm": {
        "class": "mypackage.MyLLM",
        "api_key": "...",
    }
}
```

Use via dependency injection:

```python
@service("llm", variant="my_llm")
async def my_function(llm=None):
    result = await llm.complete("Hello")
```

## Testing

KNWL is extensively tested with unit tests covering all components, strategies, and integration scenarios.

Run tests without LLM integration (fast):

```bash
uv run pytest -m "not llm"
```

Run full test suite (requires Ollama running):

```bash
uv run pytest
```

Run specific test categories:

```bash
uv run pytest -m basic           # Basic functionality tests
uv run pytest -m integration     # Integration tests
uv run pytest -m asyncio         # Async tests
```

## Examples

In the `examples/` directory, you can find various scripts demonstrating KNWL's capabilities, including:

- Basic usage and querying
- Custom LLM integration
- Advanced configuration scenarios

Use VSCode Interactive Python for best experience but you can also run this script directly.
See https://code.visualstudio.com/docs/python/jupyter-support-py for more details.


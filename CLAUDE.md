# CLAUDE.md

> Context file for AI assistants working with the Knwl codebase

## Project Overview

**Knwl** (short for "knowledge") is a flexible Graph RAG (Retrieval-Augmented Generation) Python package that provides advanced ingestion and augmentation strategies. It enables structured knowledge management through graph-based retrieval, semantic search, and LLM integration.

### Core Value Proposition

- **No external services required**: Works out of the box with Ollama (local LLM), NetworkX (graph), and JSON files
- **Protocol-based & extensible**: All components can be swapped via configuration
- **Five Graph RAG strategies**: Local, Global, Naive, Hybrid, and Self query modes
- **Dependency Injection framework**: Decorator-based DI system for clean, configurable architecture
- **Rich formatting**: Beautiful terminal (Rich), HTML, and Markdown output
- **Vendor-neutral**: Database agnostic, LLM agnostic, embedding model agnostic

### Repository Information

- **GitHub**: https://github.com/Orbifold/knwl
- **Version**: 1.8.0
- **License**: MIT
- **Python**: 3.10 - 3.12
- **Package Manager**: UV (also works with Poetry and pip)

## Architecture

### Design Principles

1. **Dependency Injection First**: All services use DI decorators (`@service`, `@singleton_service`, `@defaults`, `@inject_config`)
2. **Configuration over Code**: Runtime component swapping via JSON configuration
3. **Protocol-Based**: Components inherit from base classes and protocols
4. **Async by Default**: Most operations are async/await
5. **Type Safety**: Pydantic models throughout

### Key Architectural Patterns

#### 1. Service-Based Architecture

All major components are "services" configured in [`knwl/config.py`](knwl/config.py):

```python
{
    "service_name": {
        "default": "variant_name",
        "variant_name": {
            "class": "path.to.Class",
            "param1": "value1",
            "param2": "@/other_service/variant"  # Service redirection
        }
    }
}
```

#### 2. Dependency Injection System

Located in [`knwl/di.py`](knwl/di.py), provides decorators:

- `@service(service_name)`: Inject a new instance each time
- `@singleton_service(service_name)`: Inject a shared singleton instance
- `@defaults(service_name)`: Inject all config parameters as constructor defaults
- `@inject_config(config_path)`: Inject specific configuration values

All decorators support `override` parameter for ad-hoc configuration.

#### 3. Service Redirection

The `@/service_name/variant_name` syntax allows services to reference other services:

```json
{
  "graph_rag": {
    "local": {
      "class": "knwl.semantic.graph_rag.graph_rag.GraphRAG",
      "semantic_graph": "@/semantic_graph/memory",
      "llm": "@/llm/ollama"
    }
  }
}
```

## Directory Structure

```
knwl/
├── __init__.py          # Main exports
├── config.py            # Central configuration (25KB+, critical file)
├── di.py               # Dependency injection framework (32KB)
├── framework_base.py    # Base class for all framework components
├── knwl.py             # High-level Knwl wrapper class
├── services.py         # Service registry and instantiation
├── utils.py            # Utility functions (path resolution, etc.)
├── logging.py          # Logging configuration
│
├── chunking/           # Text chunking strategies
│   └── tiktoken_chunking.py  # Default: TiktokenChunking
│
├── cli/                # Command-line interface (Typer)
│   ├── cli.py          # Main CLI entry point
│   └── commands/       # CLI command modules
│
├── extraction/         # Graph and entity extraction
│   ├── graph_extraction.py     # Extract graphs from text
│   ├── entity_extraction.py    # Extract entities
│   └── keywords_extraction.py  # Extract keywords
│
├── format/             # Output formatting system
│   ├── formatter.py          # Main formatter dispatcher
│   ├── terminal_formatter.py # Rich-based terminal output
│   ├── html_formatter.py     # HTML output
│   └── markdown_formatter.py # Markdown output
│
├── llm/                # LLM integrations
│   ├── ollama.py       # OllamaClient (default)
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── llm_base.py     # Base protocol
│
├── models/             # Pydantic data models
│   ├── KnwlNode.py     # Graph node model
│   ├── KnwlEdge.py     # Graph edge model
│   ├── KnwlGraph.py    # Graph model
│   ├── KnwlBlob.py     # Text chunk model
│   ├── KnwlAnswer.py   # Query answer model
│   └── KnwlContext.py  # Retrieved context model
│
├── prompts/            # LLM prompt templates
│   ├── graph_extraction_prompts.py
│   ├── entity_extraction_prompts.py
│   └── rag_prompts.py
│
├── semantic/           # Graph RAG implementation
│   └── graph_rag/
│       ├── graph_rag.py           # Main GraphRAG class
│       ├── local_strategy.py      # Entity-centric retrieval
│       ├── global_strategy.py     # Relationship-centric retrieval
│       ├── naive_strategy.py      # Traditional chunk-based RAG
│       ├── hybrid_strategy.py     # Combines local + global
│       └── self_strategy.py       # LLM generates context
│
├── storage/            # Storage backends
│   ├── storage_base.py           # Base protocols
│   ├── graph_base.py             # Graph storage protocol (14KB)
│   ├── networkx_storage.py       # Default: NetworkX + GraphML (37KB)
│   ├── neo_storage.py            # Neo4j integration (21KB)
│   ├── chroma_storage.py         # ChromaDB vector storage
│   ├── json_storage.py           # JSON file storage
│   └── file_storage.py           # File blob storage
│
└── summarization/      # Text summarization services
    └── summarizer.py
```

### Important Files to Know

1. **[knwl/config.py](knwl/config.py)** (25KB): The heart of configuration
2. **[knwl/di.py](knwl/di.py)** (32KB): Dependency injection implementation
3. **[knwl/knwl.py](knwl/knwl.py)** (14KB): High-level API wrapper
4. **[knwl/storage/graph_base.py](knwl/storage/graph_base.py)**: Graph storage protocol
5. **[knwl/storage/networkx_storage.py](knwl/storage/networkx_storage.py)** (37KB): Default graph implementation

## Core Concepts

### 1. Graph RAG Strategies

Knwl implements five distinct retrieval strategies (all in [`knwl/semantic/graph_rag/`](knwl/semantic/graph_rag/)):

#### Local Strategy ([local_strategy.py](knwl/semantic/graph_rag/local_strategy.py))
- **Entity-centric retrieval**
- Extracts low-level keywords from query
- Matches against graph nodes
- Retrieves relationship neighborhood
- Use case: Questions about specific entities

#### Global Strategy ([global_strategy.py](knwl/semantic/graph_rag/global_strategy.py))
- **Relationship-centric retrieval**
- Extracts high-level keywords
- Matches against graph edges
- Retrieves connected nodes
- Use case: Questions about relationships and patterns

#### Naive Strategy ([naive_strategy.py](knwl/semantic/graph_rag/naive_strategy.py))
- **Traditional RAG**
- Semantic similarity search on text chunks
- No graph structure utilized
- Use case: Simple fact-finding

#### Hybrid Strategy ([hybrid_strategy.py](knwl/semantic/graph_rag/hybrid_strategy.py))
- **Combines Local + Global**
- Executes both in parallel
- Merges and deduplicates results
- Use case: Complex queries

#### Self Strategy ([self_strategy.py](knwl/semantic/graph_rag/self_strategy.py))
- **No retrieval**
- LLM generates context from its own knowledge
- Use case: Baseline comparisons, no relevant data

### 2. Data Models

All models are Pydantic classes in [`knwl/models/`](knwl/models/):

#### KnwlNode ([KnwlNode.py](knwl/models/KnwlNode.py))
```python
class KnwlNode(BaseModel):
    id: str              # Unique identifier
    name: str            # Entity name
    type: str            # Entity type (e.g., "Person", "Concept")
    description: str     # Detailed description
    metadata: Dict       # Additional properties
```

#### KnwlEdge ([KnwlEdge.py](knwl/models/KnwlEdge.py))
```python
class KnwlEdge(BaseModel):
    id: str              # Unique identifier
    source: str          # Source node ID
    target: str          # Target node ID
    type: str            # Relationship type
    description: str     # Relationship description
    metadata: Dict       # Additional properties
```

#### KnwlBlob ([KnwlBlob.py](knwl/models/KnwlBlob.py))
```python
class KnwlBlob(BaseModel):
    id: str              # Unique identifier
    content: str         # Text content (chunk)
    metadata: Dict       # Chunk metadata (source, position, etc.)
```

### 3. Storage System

#### Storage Types

1. **Graph Storage**: Nodes and edges (NetworkX, Neo4j, Memgraph)
2. **Vector Storage**: Embeddings for semantic search (ChromaDB)
3. **Blob Storage**: Text chunks and documents (JSON, files)
4. **KV Storage**: Key-value pairs (JSON)

#### Default Stack
- **Graph**: NetworkX in-memory with GraphML persistence
- **Vector**: ChromaDB with `all-MiniLM-L6-v2` embeddings
- **Blobs**: JSON files
- **Cache**: File-based LLM response caching

### 4. LLM Integration

Default: Ollama with Qwen2.5:7b (configurable in [`config.py`](knwl/config.py))

Supported providers:
- Ollama (default)
- OpenAI
- Anthropic
- Any custom implementation via `LLMBase` protocol

### 5. Formatting System

Located in [`knwl/format/`](knwl/format/):

```python
from knwl.format import print_knwl, format_knwl, render_knwl

# Print to terminal with Rich formatting
print_knwl(node)
print_knwl([nodes, edges, graph])

# Get formatted string
html = format_knwl(node, format_type="html")
md = format_knwl(graph, format_type="markdown")

# Save to file
render_knwl(graph, format_type="html", output_file="graph.html")
```

All Knwl models have registered formatters for terminal, HTML, and Markdown.

## Configuration System

### Configuration File

The main configuration is in [`knwl/config.py`](knwl/config.py) as `default_config` dictionary.

### Special Path Prefixes

- `$/data`: Project data directory
- `$/root`: Project root
- `$/user`: User home directory (`~/.knwl/`)
- `$/tests`: Test data directory (`tests/data/`)

### Configuration Tools

```python
from knwl.config import default_config, set_active_config
from knwl import print_knwl

# View configuration
print_knwl("@/llm/ollama")  # Print LLM config
print_knwl("@/chunking")    # Print chunking config

# Modify default config
default_config["llm"]["default"] = "openai"

# Replace entire config
set_active_config(new_config)
```

### Service Instantiation

```python
from knwl.services import services

# Get default variant
llm = services.get_service("llm")

# Get specific variant
llm = services.get_service("llm", variation="openai")

# Get singleton
graph = services.get_singleton_service("semantic_graph")

# Ad-hoc override
llm = services.get_service("llm", override={
    "llm": {
        "ollama": {
            "model": "gemma2:7b",
            "temperature": 0.5
        }
    }
})
```

## Common Workflows

### 1. Adding Facts to Knowledge Graph

```python
from knwl import Knwl

async def add_knowledge():
    knwl = Knwl()

    # Add fact (extracts graph automatically)
    await knwl.add_fact(
        "gravity",
        "Gravity is a universal force.",
        id="fact1"
    )

    # Connect entities
    await knwl.connect(
        source_name="gravity",
        target_name="photosynthesis",
        relation="Both are natural processes"
    )
```

### 2. Querying with Graph RAG

```python
from knwl import Knwl

async def query():
    knwl = Knwl()

    # Ask question (uses Local strategy by default)
    answer = await knwl.ask("What is photosynthesis?")
    print_knwl(answer.answer)

    # Get augmented context only
    context = await knwl.augment("What is photosynthesis?")
    print_knwl(context)
```

### 3. Using Different Strategies

```python
from knwl.semantic.graph_rag import GraphRAG
from knwl.services import services

# Get GraphRAG service
graph_rag = services.get_service("graph_rag")

# Query with specific strategy
local_answer = await graph_rag.ask("query", strategy="local")
global_answer = await graph_rag.ask("query", strategy="global")
hybrid_answer = await graph_rag.ask("query", strategy="hybrid")
naive_answer = await graph_rag.ask("query", strategy="naive")
```

### 4. Custom Service Configuration

```python
from knwl.di import service, defaults

# Inject service
@service("llm")
async def use_llm(llm=None):
    return await llm.ask("What is AI?")

# Inject defaults
@defaults("graph_extraction")
class CustomExtractor:
    def __init__(self, llm=None, mode=None):
        self.llm = llm
        self.mode = mode
```

### 5. Working with Storage Directly

```python
from knwl.services import services
from knwl.models import KnwlNode, KnwlEdge

# Get graph storage
graph = services.get_singleton_service("semantic_graph")

# Add nodes
node = KnwlNode(
    id="n1",
    name="AI",
    type="Concept",
    description="Artificial Intelligence"
)
await graph.add_node(node)

# Add edges
edge = KnwlEdge(
    id="e1",
    source="n1",
    target="n2",
    type="related_to",
    description="AI is related to ML"
)
await graph.add_edge(edge)

# Query
nodes = await graph.get_nodes_by_type("Concept")
neighbors = await graph.get_neighbors("n1")
```

## Testing

### Test Structure

```
tests/
├── test_di.py                    # DI system tests
├── test_storage/                 # Storage backend tests
├── test_extraction/              # Extraction tests
├── test_semantic/                # Graph RAG strategy tests
├── test_models.py                # Pydantic model tests
└── library/                      # Test data (Wikipedia articles)
```

### Running Tests

```bash
# Fast tests (no LLM)
uv run pytest -m "not llm"

# All tests (requires Ollama, API keys)
uv run pytest

# With coverage
uv run pytest --cov=knwl --cov-report=html
```

### Test Markers

- `@pytest.mark.llm`: Tests requiring LLM
- `@pytest.mark.asyncio`: Async tests
- `@pytest.mark.integration`: Integration tests

## Development Guidelines

### Code Style

1. **Async by default**: Most operations should be async
2. **Type hints**: Always include type hints
3. **Pydantic models**: Use Pydantic for all data models
4. **DI decorators**: Use DI decorators instead of manual instantiation
5. **Configuration**: Prefer configuration over hardcoding

### Adding a New Service

1. Create the service class inheriting from appropriate base
2. Add service configuration to [`config.py`](knwl/config.py)
3. Register in [`services.py`](knwl/services.py) if needed
4. Add tests in `tests/`
5. Update documentation

### Adding a New Storage Backend

1. Implement the protocol from [`storage/storage_base.py`](knwl/storage/storage_base.py) or [`storage/graph_base.py`](knwl/storage/graph_base.py)
2. Add configuration variant in [`config.py`](knwl/config.py)
3. Add integration tests
4. Update README with setup instructions

### Adding a New RAG Strategy

1. Create strategy class in [`semantic/graph_rag/`](knwl/semantic/graph_rag/)
2. Implement `query()` method returning `KnwlContext`
3. Register in [`graph_rag.py`](knwl/semantic/graph_rag/graph_rag.py) strategy mapping
4. Add tests with sample queries
5. Document use cases

## Common Issues

### ChromaDB PanicException
**Symptom**: `PanicException: range start index 10 out of range`
**Cause**: Corrupted ChromaDB collection
**Fix**: Delete vector storage directory (usually `~/.knwl/default/vector/`)

### LLM Timeout
**Symptom**: Extraction times out
**Cause**: Model too small (e.g., gemma3:4b)
**Fix**: Use larger model (qwen2.5:7b recommended) or increase timeout

### Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'knwl.X'`
**Cause**: Package not installed in editable mode
**Fix**: `uv add --editable .` from project root

## CLI Commands

```bash
# Search knowledge base
knwl search "query text"

# View configuration
knwl config tree
knwl config summary

# For more commands see knwl --help
```

## Key Dependencies

- **torch**: PyTorch for embeddings
- **networkx**: Default graph storage
- **chromadb**: Vector database
- **tiktoken**: Text chunking
- **ollama**: Default LLM client
- **pydantic**: Data validation
- **rich**: Terminal formatting
- **typer**: CLI framework

## Optional Dependencies

```bash
# Neo4j support
uv sync --group neo4j

# Development tools
uv sync --group dev
```

## Resources

- **README**: Comprehensive feature overview and examples
- **Journal**: Design documents in `journal/` directory
- **Examples**: Usage examples in `examples/` directory
- **Benchmarks**: Performance evaluation in `benchmarks/`

## Architecture Insights

### Why Dependency Injection?

- **Flexibility**: Swap implementations without code changes
- **Testability**: Easy to mock services in tests
- **Configuration**: Centralized configuration management
- **Extensibility**: Add new services without modifying existing code

### Why Graph RAG?

- **Relationships matter**: Vector similarity misses explicit connections
- **Domain expertise**: Graphs can encode expert knowledge
- **Incremental updates**: Add nodes/edges without re-vectorizing
- **Explainability**: Trace answers back to graph paths
- **Multi-hop reasoning**: Traverse complex relationships

### Why Protocol-Based?

- **Vendor neutrality**: Not locked to specific providers
- **Duck typing**: Easy to implement custom backends
- **Type safety**: Protocols provide static type checking
- **Documentation**: Protocols serve as interface documentation

## Tips for AI Assistants

1. **Configuration is key**: Always check [`config.py`](knwl/config.py) to understand service setup
2. **DI everywhere**: Use `services.get_service()` or DI decorators, avoid direct instantiation
3. **Async patterns**: Most methods are async, use `await`
4. **Type hints help**: Check Pydantic models in [`models/`](knwl/models/) for data structures
5. **Test before suggesting**: Check [`tests/`](tests/) for usage patterns
6. **Follow existing patterns**: Look at similar components before creating new ones
7. **Configuration over code**: Suggest config changes before code changes
8. **Storage is abstracted**: Don't assume NetworkX, use graph protocol methods

## Contact

- **Email**: info@orbifold.net
- **Website**: https://orbifold.net
- **Company**: Orbifold Consulting (Belgium)

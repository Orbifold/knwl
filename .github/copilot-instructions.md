# KNWL AI Agent Instructions

**v2 branch is under active development** - major architectural changes from v1.

## Architecture Overview

KNWL is a Graph RAG Python package with pluggable components orchestrated through three core systems:

### 1. Configuration System (`knwl/config.py`)

Hierarchical dictionary with **service variants** enabling runtime component swapping:

```python
"llm": {
    "default": "ollama",           # specifies default variant
    "ollama": {"class": "knwl.llm.ollama.OllamaClient", "model": "o14", ...},
    "openai": {"class": "knwl.llm.openai.OpenAIClient", "model": "gpt-4o-mini", ...}
}
```

**Key features:**
- **Cross-references**: `"@/llm/ollama"` resolves to config at `llm.ollama`
- **Path placeholders**: `$root` (project root), `$/tests` (tests/data), `$/data` expand dynamically
- **Deep merge**: `override` parameter merges recursively, doesn't replace entire sections
- Access via `get_config("llm", "model", override={...})`

### 2. Dependency Injection (`knwl/di.py`)

Decorator-based DI eliminates manual service instantiation:

```python
@service("llm", variant="ollama", param_name="ai")
@singleton_service("graph", variant="nx")  # reuses same instance
@inject_config("api.host", "api.port")     # pulls config values
@defaults("json")                          # injects service's default config
async def process(text: str, ai=None, graph=None, host=None, port=None):
    # All params automatically injected from config
    pass
```

All decorators accept `override` dict for context-specific config without modifying defaults.

### 3. Services Registry (`knwl/services.py`)

Dynamic class loading via config:
- Service definitions must include `"class": "full.module.path.ClassName"`
- Parse names: `services.get_service("vector/chroma")` or `("vector", "chroma")`
- Singletons cached by service+variant+override hash

### 4. Framework Base (`knwl/framework_base.py`)

All components inherit from `FrameworkBase` (ABC) providing:
- `get_service(name, variant)` - fetch any configured service
- `get_llm(variant)` - shorthand for LLM service
- `ensure_path_exists(path)` - cross-platform path handling
- `id` - unique UUID per instance

## Core Data Flow

```
Input Text → Documents → Chunks → Graph Extraction → SemanticGraph → Vector Storage
                                      ↓
                              KnwlExtraction (nodes+edges)
                                      ↓
                              Merge & Summarize → Storage (JSON/Chroma/NetworkX)
```

**Main orchestration** in `GraphRAG` class (`knwl/semantic/graph_rag/graph_rag.py`):

1. **`ingest(inputs)`** - Primary ingestion pipeline:
   - Processes `KnwlInput` → chunks text → extracts graph → stores in semantic graph
   - Returns `KnwlIngestion` with metadata
   - Optionally chunks and stores text if `ragger` is provided

2. **`augment(inputs, params)`** - Query/augmentation with multiple strategies:
   - **local**: Keywords → nodes → retrieve neighborhood + chunks
   - **global**: Keywords → edges → retrieve endpoints + edge chunks  
   - **naive**: Direct semantic chunk retrieval (no graph)
   - **hybrid**: Combines local + global contexts
   - Returns `KnwlContext` with augmented context and references

## Models (`knwl/models/`)

**All models are immutable Pydantic BaseModels** (`model_config = {"frozen": True}`):

- Auto-generated `id` via hash of key fields (e.g., `KnwlNode.hash_keys(name, type)`)
- Serialize with `model_dump(mode="json")`
- Update via `model.model_copy(update={"field": new_value})`

**Key models:**
- `KnwlNode` - graph vertices (name, type, description, chunk_ids)
- `KnwlEdge` - graph edges (source_id, targetId, description, keywords, weight)
- `KnwlExtraction` - raw LLM extraction (dicts of nodes/edges keyed by name)
- `KnwlGraph` - final graph (lists of `KnwlNode`/`KnwlEdge`)
- `KnwlChunk`, `KnwlDocument`, `KnwlInput` - pipeline data structures

## Component Architecture

**Base classes define pluggable interfaces:**
- `LLMBase` → `OllamaClient`, `OpenAIClient`
- `ChunkingBase` → `TiktokenChunking`
- `StorageBase` → `JsonStorage`, `SqliteStorage`
- `VectorStorageBase` → `ChromaStorage`
- `GraphStorageBase` → `NetworkXGraphStorage`
- `GraphExtractionBase` → `BasicGraphExtraction`, `GleanGraphExtraction`
- `GraphRAGBase` → `GraphRAG`
- `SemanticGraphBase` → `SemanticGraph`
- `RagBase` → `RagStore`
- `GragStrategyBase` → `LocalGragStrategy`, `GlobalGragStrategy`, `NaiveGragStrategy`, `HybridGragStrategy`
- `EntityExtractionBase`, `KeywordsExtractionBase`, `FormatterBase`, etc.

**Storage namespaces** isolate data:
```python
JsonStorage(namespace="documents")   # → {path}/documents.json
ChromaStorage(namespace="nodes")     # → Chroma collection "nodes"
NetworkXGraphStorage(namespace="kg") # → {path}/kg.graphml
```

## Testing

**Fast tests** (skip LLM integration):
```bash
uv run pytest -m "not llm"
```

**Full suite** (requires Ollama running):
```bash
uv run pytest
```

**Test markers** (`pytest.ini`):
- `@pytest.mark.llm` - needs Ollama/LLM
- `@pytest.mark.asyncio` - async test
- `@pytest.mark.integration` - external services
- `@pytest.mark.slow` - long-running
- `@pytest.mark.basic` - basic tests that don't require external services

**Important**: DI container persists between tests - clear state in `setup_method()` if tests interfere.

## Development Patterns

### Adding a Service Variant

1. **Create class** inheriting from base (e.g., `LLMBase`)
2. **Add to config** in `knwl/config.py`:
   ```python
   "llm": {
       "default": "ollama",
       "my_llm": {
           "class": "knwl.llm.my_llm.MyLLMClient",
           "api_key": "...",
           "model": "..."
       }
   }
   ```
3. **Use via DI**: `@service("llm", variant="my_llm")`

### Working with Immutable Models

```python
# ❌ WRONG - models are frozen
node.description = "new desc"

# ✅ CORRECT
updated_node = node.model_copy(update={"description": "new desc"})
```

### Async Parallelism

Prefer `asyncio.gather()` for concurrent operations:
```python
nodes = await asyncio.gather(*[
    self.merge_nodes_into_graph(k, v) 
    for k, v in extraction.nodes.items()
])
```

### Config Overrides

```python
# Override specific config without modifying defaults
override = {"llm": {"temperature": 0.5}}

@service("llm", override=override)
async def my_func(llm=None):
    # llm uses temperature=0.5 instead of default
    pass
```

## Common Pitfalls

1. **Frozen models**: Use `.model_copy(update={...})` not direct assignment
2. **Config references**: `@/path/to/service` only works in config dict, not arbitrary strings
3. **Service class paths**: Must be importable Python paths (e.g., `knwl.llm.ollama.OllamaClient`)
4. **DI container state**: Persists across tests - may need cleanup
5. **Path handling**: Always use `ensure_path_exists()` or `get_full_path()` from `FrameworkBase`
6. **Namespace confusion**: Storage instances with same class but different namespaces are distinct

## Entry Points

- **Library**: `from knwl.semantic.graph_rag.graph_rag import GraphRAG; rag = GraphRAG(...); await rag.ingest(input)`
- **API**: `api/main.py` - FastAPI REST service (uvicorn, configurable workers)

**Running API**:
```bash
# Development (auto-reload)
python api/main.py  # reads config from api.host, api.port, api.development

# Production
uvicorn api.main:app --host 0.0.0.0 --port 9000 --workers 8
```

## Project Management

**Package manager**: `uv` (not pip/poetry)
- Dependencies in `pyproject.toml`
- Install: `uv sync`
- Run scripts: `uv run pytest`, `uv run python cli.py`

**Design journal**: `journal/*.md` explains architectural decisions
- `DependencyInjection.md` - DI framework rationale
- `GraphRAG.md`, `GraphExtraction.md` - Graph RAG strategy
- `Models.md` - Data model design

## Key Files for Reference

- `knwl/semantic/graph_rag/graph_rag.py` - Main `GraphRAG` orchestration class
- `knwl/di.py` - DI framework (~930 lines, see `tests/test_di.py`)
- `knwl/config.py` - Config structure, `get_config()`, merge logic
- `knwl/services.py` - Service registry, dynamic class loading
- `knwl/framework_base.py` - Base class for all components
- `knwl/prompts/extraction_prompts.py` - LLM prompts for entity extraction
- `knwl/semantic/graph/semantic_graph.py` - Semantic graph implementation
- `knwl/semantic/rag/rag_store.py` - RAG store for chunk management
- `tests/fixtures.py` - Test data and shared fixtures

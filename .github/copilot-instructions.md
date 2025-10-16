# KNWL AI Agent Instructions

**v2 branch is under active development** - major architectural changes from v1.

## Architecture Overview

KNWL is a Graph RAG Python package with pluggable components coordinated through:

1. **Configuration System** (`knwl/config.py`): Hierarchical dict with service variants
   - Reference syntax: `"@/llm/ollama"` creates cross-references within config
   - Path placeholders: `$root`, `$test` expand to system paths
   - Deep merge on override (not replacement)

2. **Dependency Injection** (`knwl/di.py`): Decorator-based service injection
   - `@service("llm", variant="ollama", param_name="ai")` - creates service instance
   - `@singleton_service("graph", variant="nx")` - reuses instances
   - `@inject_config("api.host", "api.port")` - pulls config values
   - `@defaults("json")` - injects defaults from service config
   - All decorators support `override` param for context-specific config

3. **Services Registry** (`knwl/services.py`): Dynamic class loading from config
   - Format: `{"class": "knwl.llm.ollama.OllamaClient", ...}`
   - Default variant specified via `"default": "variant_name"`
   - Parse service names: `"vector/chroma"` or `("vector", "chroma")`

4. **Framework Base** (`knwl/framework_base.py`): All components inherit from `FrameworkBase`
   - Provides `get_service()`, `get_llm()`, `ensure_path_exists()`
   - Every instance has unique `id` UUID

## Core Data Flow

```
Input Text → Documents → Chunks → Graph Extraction → KnwlGraph → Vector Storage
                                      ↓
                              KnwlExtraction (nodes+edges)
                                      ↓
                              Merge & Summarize → Storage (JSON/Chroma/NetworkX)
```

Main entry point: `Knwl.insert()` or `Knwl.input()` in `knwl.py`:
- Stores sources → chunks text → extracts entities/edges → merges to graph → vectorizes
- Use `basic_rag=True` to skip graph construction and only chunk

Query modes (see `Knwl.query()`):
- **local**: Match keywords to nodes, retrieve neighborhood + chunks
- **global**: Match keywords to edges, retrieve endpoints + edge chunks  
- **naive**: Direct chunk retrieval without graph
- **hybrid**: Combines local + global contexts

## Models (`knwl/models/`)

All models are **immutable Pydantic models** with:
- Auto-generated `id` from hash of key fields
- `model_dump(mode="json")` for serialization
- Example: `KnwlNode(name="AI", type="Concept")` → hashed id

Key models:
- `KnwlNode` - graph vertices (name + type + description + chunk_ids)
- `KnwlEdge` - graph edges (source + target + description)
- `KnwlExtraction` - raw extraction output (dicts of nodes/edges by name)
- `KnwlGraph` - final graph (lists of KnwlNode/KnwlEdge)

## Testing

Run tests avoiding LLM calls (fast):
```bash
uv run pytest -m "not llm"
```

Full test suite:
```bash
uv run pytest
```

Test markers in `pytest.ini`:
- `@pytest.mark.llm` - requires Ollama running
- `@pytest.mark.asyncio` - async test functions
- `@pytest.mark.integration` - external service deps

## Development Patterns

### Adding a New Service Component

1. Create class inheriting from appropriate base (e.g., `LLMBase`, `ChunkingBase`)
2. Add config to `default_config` in `knwl/config.py`:
   ```python
   "my_service": {
       "default": "variant1",
       "variant1": {
           "class": "knwl.module.MyClass",
           "param1": "value"
       }
   }
   ```
3. Use `@service("my_service")` decorator to inject

### Using DI in Functions

```python
from knwl.di import service, inject_config

@service("llm", variant="ollama")
@inject_config("chunking.tiktoken.chunk_size")
async def process(text: str, llm=None, chunk_size=None):
    # llm and chunk_size automatically injected
    pass
```

### Storage Namespaces

Storage classes use namespaces to isolate data:
```python
JsonStorage(namespace="documents")  # → path becomes .../documents.json
VectorStorageBase(namespace="nodes")  # → Chroma collection "nodes"
```

### Async Pattern

Most operations are async - use `await` and `asyncio.gather()` for parallelism:
```python
nodes = await asyncio.gather(*[self.merge_nodes_into_graph(k, v) for k, v in g.nodes.items()])
```

## Common Pitfalls

- Don't modify Pydantic models in place (they're frozen) - use `.model_copy(update={...})`
- Config references (`@/path`) only work within `get_config()`, not arbitrary strings
- Service classes must have `class` key in config pointing to importable path
- Test cleanup: DI container persists between tests - clear in `setup_method()` if needed
- Path handling: Use `get_full_path()` or `ensure_path_exists()` for cross-platform compatibility

## Entry Points

- **CLI**: `cli.py` - Click-based commands
- **API**: `api/main.py` - FastAPI REST service  
- **Library**: `from knwl.knwl import Knwl`

## Key Files for Reference

- `knwl.py` - Main orchestration class
- `knwl/di.py` - DI framework (300+ lines, well-tested in `tests/test_di.py`)
- `knwl/config.py` - Configuration structure and `get_config()`
- `knwl/prompts/extraction_prompts.py` - LLM prompts for entity/graph extraction
- `journal/*.md` - Design docs explaining architectural decisions

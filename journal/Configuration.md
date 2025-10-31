Knwl has an intricate [[DependencyInjection]] system which allows for flexible configuration of its services. Instead of having defaults for the constructor parameters of each service, Knwl uses a centralized configuration object to manage dependencies. This design choice enables easier testing, customization, and extension of the services without modifying their internal implementations.

For example, the default chunking is based on Tiktoken and happens in the `TiktokenChunkin` class. There are essentially three parameters that can be configured for chunking:

- the chunk size
- the chunk overlap
- the chunking model

In the `config.py` file you will find:

```json
{
  "chunking": {
    "default": "tiktoken",
    "tiktoken": {
      "class": "knwl.chunking.TiktokenChunking",
      "model": "gpt-4o-mini",
      "chunk_size": 1024,
      "chunk_overlap": 128
    }
  }
}
```

You can moddigy these paramters to change the default chunking behavior of Knwl.

Alternatively you can override the config when instantiating the chunking service:

```python
from knwl.services import services
chunker = services.get_service("chunking", override={
    "chunking"{
        "tiktoken": {
            "chunk_size": 2048,
            "chunk_overlap": 256,
        }
    }
})
```

This overrides the default chunking configuration but you can also defines variations (variants) like so:

```json
{
  "chunking": {
    "default": "tiktoken",
    "tiktoken": {
      "class": "knwl.chunking.TiktokenChunking",
      "model": "gpt-4o-mini",
      "chunk_size": 1024,
      "chunk_overlap": 128
    },
    "tiktoken-large": {
      "class": "knwl.chunking.TiktokenChunking",
      "model": "gpt-4o-mini",
      "chunk_size": 2048,
      "chunk_overlap": 256
  }
}
```

Then you can instantiate the chunking service with the "tiktoken-large" variant:

```python
from knwl.services import services
chunker = services.get_service("chunking", "tiktoken-large")
```

If you have lots of configurations to override, you can also replace the active or base configuration entirely using the `set_active_config` function from `knwl.config`:

```python
from knwl.config import set_active_config
new_config = {
  "chunking": {
    "default": "tiktoken-large",
    "tiktoken": {
      "class": "knwl.chunking.TiktokenChunking",
      "model": "gpt-4o-mini",
      "chunk_size": 1024,
      "chunk_overlap": 128
    },
    "tiktoken-large": {
      "class": "knwl.chunking.TiktokenChunking",
      "model": "gpt-4o-mini",
      "chunk_size": 2048,
      "chunk_overlap": 256
    }
  }
}
set_active_config(new_config)
```

If you want this configuration to be the default for all chunking services, you can change the "default" key in the config to point to "tiktoken-large":

```json
{
  "chunking": {
    "default": "tiktoken-large",
    ...
  }
}
```

## Redirecting

The inter-dependency of services means that a service configuration is required in multiple place. You can re-use or redirect a configuration by using the `@/` prefix. For example, if you want to use the same chunking configuration for a different service, you can do:

```json
{
  "some_other_service": {
    "chunking": "@/chunking/tiktoken"
  }
}
```

More concretely, you will see that the default graph RAG service is configured like so:

```json
{
  "graph_rag": {
    "default": "local",
    "local": {
      "class": "knwl.semantic.graph_rag.graph_rag.GraphRAG",
      "semantic_graph": "@/semantic_graph/memory",
      "ragger": "@/rag_store",
      "graph_extractor": "@/graph_extraction/basic",
      "keywords_extractor": "@/keywords_extraction"
    }
  }
}
```

The syntax `@/semantic_graph/memory` tells Knwl to use the configuration defined for the `memory` variant of the `semantic_graph` service. This allows for consistent configuration across different services without duplication.
If there is no variant specified, Knwl will use the default variant for that service. The `@/rag_store` in the example above will resolve to the default variant of the `rag_store` service.

# Print

The `print_knwl` function is a generic printing utility for various Knwl objects. It also allows to print configuration details of services. For example, to print the configuration of the chunking service, you can do:

```python
from knwl import print_knwl
print_knwl("@/chunking")
```

or the default Ollama model:

```python
print_knwl("@/llm/ollama/model")
```

The configuration can contains redirections but the print will resolve them for clarity.

There are special paths in Knwl that can be used to reference different directories. These paths are prefixed with `$` and are resolved to specific locations in the file system. The special paths include:

- `$/data`: This path points to the `data` directory within the Knwl project. It is typically used to store datasets or other data files required by Knwl.
- `$/root`: This path points to the root directory of the Knwl project. It can be used to reference files or directories located at the top level of the Knwl project.
- `$/user`: This path points to a user-specific directory, typically located in the user's home directory. It is used to store user-specific configurations or data related to Knwl.
- `$/tests`: This path points to the `tests/data` directory within the Knwl project. It is used to store test datasets or files required for testing Knwl functionalities.
  These special paths can be used in configuration files or code to easily reference important directories without hardcoding absolute paths. The Knwl utility functions will resolve these paths to their actual locations when needed.

You can test the special paths using the `print_knwl` function like so:

```python
print_knwl("$/user/abc")
print_knwl("$/data/xyz")
print_knwl("$/tests/xyz")
```

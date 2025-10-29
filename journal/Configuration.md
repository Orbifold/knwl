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

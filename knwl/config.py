# ============================================================================================
# The settings are as much settings as recipe in the case of knwl.
# By enabling/disabling certain features here, you can change the behavior of knwl.
# ============================================================================================

default_config = {
    "api": {
        "development": True,
        "host": "0.0.0.0",
        "port": 9000,
    },
    "logging": {"enabled": True, "level": "INFO", "path": "$root/knwl.log"},
    "chunking": {
        "default": "tiktoken",
        "tiktoken": {
            "class": "knwl.chunking.TiktokenChunking",
            "model": "gpt-4o-mini",
            "size": 1024,
            "overlap": 128,
        },
    },
    "summarization": {
        "default": "ollama",
        "concat": {
            "class": "knwl.summarization.concat.SimpleConcatenation",
            "max_tokens": 500,
        },
        "ollama": {
            "class": "knwl.summarization.ollama.OllamaSummarization",
            "model": "gemma3:4b",
            "max_tokens": 150,
            "chunker": "tiktoken",
        },
    },
    "entity_extraction": {
        "default": "basic",
        "basic": {
            "class": "knwl.extraction.basic_entity_extraction.BasicEntityExtraction",
            "llm": "gemma-small",
        },
    },
    "graph_extraction": {
        "default": "basic",
        "basic": {
            "class": "knwl.extraction.basic_graph_extraction.BasicGraphExtraction",
            "mode": "full",  # fast or full
            "llm": "gemma-small",
        },
        "glean": {
            "class": "knwl.extraction.glean_graph_extraction.GleanGraphExtraction",
            "llm": "ollama",
            "mode": "full",  # fast or full
            "max_glean": 3,
        },
    },
    "semantic": {
        "default": "local",
        "graph-rag": {
            "class": "knwl.semantic.graph_rag.GraphRAG",
            "node-embeddings": "vector/nodes",  # embeddings of the nodes
            "edge-embeddings": "vector/edges",  # embeddings of the edges
            "document-store": "json/document-store",  # for document data
            "chunk-store": "json/chunk-store",  # for chunks data
        },

        "local": {
            "graph": {
                "graph-store": "graph/graph-store",  # the topology
                "node-embeddings": "vector/nodes",  # the node embeddings
                "edge-embeddings": "vector/edges",  # the edge embeddings
                "summarization": "summarization/ollama",  # how to summarize long texts
             }
        }
    },
    "llm": {
        "default": "ollama",
        "ollama": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "qwen2.5:14b",
            "caching": "json",
            "temperature": 0.1,
            "context_window": 32768,
        },
        "openai": {
            "class": "knwl.llm.openai.OpenAIClient",
            "model": "gpt-4o-mini",
            "caching": "json",
            "temperature": 0.1,
            "context_window": 32768,
        },
        "gemma-small": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "gemma3:4b",
            "caching": "json",
            "temperature": 0.1,
            "context_window": 32768,
        },
    },
    "llm_caching": {
        "default": "json",
        "json": {
            "class": "knwl.llm.json_llm_cache.JsonLLMCache",
            "path": "$test/llm.json",
        },
    },
    "vector": {
        "default": "chroma",
        "chroma": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$test/vector",
            "collection": "default",
            "metadata": [],
        },
        "nodes": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$test/graphrag",
            "collection": "nodes",
        },
        "edges": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$test/graphrag",
            "collection": "edges",
        },
    },
    "graph": {
        "default": "nx",
        "nx": {
            "class": "knwl.storage.networkx_storage.NetworkXGraphStorage",
            "format": "graphml",
            "memory": False,
            "path": "$test/graph.graphml",
        },
        "graph-store": {
            "class": "knwl.storage.networkx_storage.NetworkXGraphStorage",
            "format": "graphml",
            "memory": False,
            "path": "$test/graphrag/graph.graphml",
        },
    },
    "json": {
        "default": "basic",
        "basic": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$test/data.json",
        },
        "node-store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$test/graphrag/node_store.json",
        },
        "edge-store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$test/graphrag/edge_store.json",
        },
        "document-store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$test/graphrag/document_store.json",
        },
        "chunk-store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$test/graphrag/chunk_store.json",
        },
    },
}


def merge_configs(source: dict, destination: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge_configs(value, node)
        else:
            destination[key] = value
    return destination


def get_config(*keys, default=None, config=None, override=None):
    """
    Get (recursively) a configuration value from the settings dictionary.
    Args:
        *key: A variable number of string arguments representing the keys to access the nested configuration.
        default: The default value to return if the specified key path does not exist. Defaults to None.
        config: The configuration dictionary to use. If None, the global config will be used. Defaults to None.
        override: An optional dictionary to override the default config for this lookup. Defaults to None.
    @example:

    >>> get_config("llm", "model")
    'gemma3:4b'

    >>> get_config("llm", "non_existent_key", default="default_value")
    'default_value'
    """
    # the config should not be changed outside
    cloned_config = (config or default_config).copy()
    if len(keys) == 0:
        return cloned_config
    if override is not None:
        cloned_config = merge_configs(override, cloned_config)
    if len(keys) == 1:
        return cloned_config.get(keys[0], default)
    else:
        current = cloned_config
        # drill down into the nested dictionary
        for k in keys:
            current = current.get(k, None)
            if current is None:
                return default
        return current

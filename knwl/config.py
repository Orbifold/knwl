# ============================================================================================
# The settings are as much settings as recipe in the case of knwl.
# By enabling/disabling certain features here, you can change the behavior of knwl.
# ============================================================================================
import copy

from knwl.utils import get_full_path

default_config = {
    "logging": {"enabled": True, "level": "ERROR", "path": "$/user/default/knwl.log"},
    "chunking": {
        "default": "tiktoken",
        "tiktoken": {
            "class": "knwl.chunking.TiktokenChunking",
            "model": "gpt-4o-mini",
            "chunk_size": 1024,
            "chunk_overlap": 128,
        },
    },
    "chunk_store": {
        "default": "basic",
        "basic": {
            "class": "knwl.semantic.rag.chunk_store.ChunkStore",
            "chunker": "@/chunking/tiktoken",
            "chunk_embeddings": "@/vector/chunks",
            "chunk_storage": "@/json/chunk_store",
        },
    },
    "document_store": {
        "default": "basic",
        "basic": {
            "class": "knwl.semantic.rag.document_store.DocumentStore",
            "document_storage": "@/json/document_store",
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
            "llm": "@/llm/gemma_small",
            "max_tokens": 150,
            "chunker": "@/chunking/tiktoken",
        },
    },
    "entity_extraction": {
        "default": "basic",
        "basic": {
            "class": "knwl.extraction.basic_entity_extraction.BasicEntityExtraction",
            "llm": "@/llm/openai",
        },
    },
    "keywords_extraction": {
        "default": "basic",
        "basic": {
            "class": "knwl.extraction.basic_keywords_extraction.BasicKeywordsExtraction",
            "llm": "@/llm/ollama",
        },
    },
    "graph_extraction": {
        "default": "basic",
        "basic": {
            "class": "knwl.extraction.basic_graph_extraction.BasicGraphExtraction",
            "mode": "full",  # fast or full
            "llm": "@/llm/openai",
        },
    },
    "glean_graph_extraction": {
        "default": "max3",
        "max3": {
            "class": "knwl.extraction.glean_graph_extraction.GleanGraphExtraction",
            "llm": "@/llm/ollama",
            "max_glean": 3,
        },
    },
    "semantic_graph": {
        "default": "memory",
        "local": {
            "class": "knwl.semantic.graph.semantic_graph.SemanticGraph",
            "graph_store": "@/graph/nx",  # the topology
            "node_embeddings": "@/vector/nodes",  # the node embeddings
            "edge_embeddings": "@/vector/edges",  # the edge embeddings
            "summarization": "@/summarization/ollama",  # how to summarize long texts
        },
        "memory": {
            "class": "knwl.semantic.graph.semantic_graph.SemanticGraph",
            "graph_store": "@/graph/memory",  # the topology
            "node_embeddings": "@/vector/memory",  # the node embeddings
            "edge_embeddings": "@/vector/memory",  # the edge embeddings
            "summarization": "@/summarization/ollama",  # how to summarize long texts
        },
    },
    "llm": {
        "default": "ollama",
        "ollama": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "gpt-oss:20b",
            "caching_service": "@/llm_caching/user",
            "temperature": 0.1,
            "context_window": 32768,
        },
        "openai": {
            "class": "knwl.llm.openai.OpenAIClient",
            "model": "gpt-4o-mini",
            "caching_service": "@/llm_caching/user",
            "temperature": 0.1,
            "context_window": 32768,
        },
        "gemma_small": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "gemma3:4b",
            "caching_service": "@/llm_caching/user",
            "temperature": 0.1,
            "context_window": 32768,
        },
    },
    "llm_caching": {
        "default": "user",
        "tests": {
            "class": "knwl.llm.json_llm_cache.JsonLLMCache",
            "path": "$/tests/llm.json",
        },
        "user": {
            "class": "knwl.llm.json_llm_cache.JsonLLMCache",
            "path": "$/user/default/llm_cache.json",
        },
    },
    "vector": {
        "default": "chroma",
        "chroma": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$/tests/vector",
            "collection_name": "default",
            "metadata": [],
        },
        "nodes": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$/tests/graphrag",
            "collection_name": "nodes",
        },
        "edges": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$/tests/graphrag",
            "collection_name": "edges",
        },
        "memory": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": True,
            "collection_name": "default",
        },
        "chunks": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": True,
            "collection_name": "chunks",
        },
    },
    "graph": {
        "default": "nx",
        "nx": {
            "class": "knwl.storage.networkx_storage.NetworkXGraphStorage",
            "format": "graphml",
            "memory": False,
            "path": "$/tests/graph.graphml",
        },
        "memory": {
            "class": "knwl.storage.networkx_storage.NetworkXGraphStorage",
            "format": "graphml",
            "memory": True,
        },
    },
    "json": {
        "default": "basic",
        "basic": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$/data/data.json",
        },
        "node_store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$/tests/graphrag/node_store.json",
        },
        "edge_store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$/tests/graphrag/edge_store.json",
        },
        "document_store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$/tests/graphrag/document_store.json",
        },
        "chunk_store": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$/tests/graphrag/chunk_store.json",
        },
    },
    "blob": {
        "default": "file_system",
        "file_system": {
            "class": "knwl.storage.file_storage.FileStorage",
            "base_path": "$/data/blobs",
        },
    },
    "graph_rag": {
        "default": "local",
        "local": {
            "class": "knwl.semantic.graph_rag.graph_rag.GraphRAG",
            "semantic_graph": "@/semantic_graph/memory",
            "ragger": "@/rag_store",
            "graph_extractor": "@/graph_extraction/basic",
            "keywords_extractor": "@/keywords_extraction",
        },
    },
    "rag_store": {
        "default": "basic",
        "basic": {
            "class": "knwl.semantic.rag.rag_store.RagStore",
            "document_store": "@/document_store",
            "chunk_store": "@/chunk_store",
            "chunker": "@/chunking/tiktoken",
            "auto_chunk": True,
        },
    },
}


def merge_configs(override: dict, default_config: dict) -> dict:
    """
    Recursively merge two configuration dictionaries.

    This function merges an override configuration dictionary into a default configuration
    dictionary. For nested dictionaries, the merge is performed recursively. Non-dictionary
    values in the override will replace corresponding values in the default configuration.

    Args:
        override (dict): The configuration dictionary containing values to override defaults.
            Can be None or empty, in which case the default_config is returned unchanged.
        default_config (dict): The base configuration dictionary that will be updated with
            override values. This dictionary is modified in place.

    Returns:
        dict: The merged configuration dictionary (same object as default_config after modification).

    Raises:
        ValueError: If override is not None and not a dictionary.
        ValueError: If default_config is not None and not a dictionary.

    Examples:
        ```python
        default = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            }
        }
        override = {
            "b": {
                "c": 20
            },
            "e": 4
        }
        merged = merge_configs(override, default)
        # merged is now:
        # {
        #     "a": 1,
        #     "b": {
        #         "c": 20,
        #         "d": 3
        #     },
        #     "e": 4
        # }
        ```
    """
    if override is None:
        return default_config
    if not isinstance(override, dict):
        raise ValueError("merge_configs: override must be a dictionary")
    if default_config is None:
        return override
    if not isinstance(default_config, dict):
        raise ValueError("merge_configs: default_config must be a dictionary")

    for key, value in override.items():
        if isinstance(value, dict):
            # get node or create one
            node = default_config.setdefault(key, {})
            merge_configs(value, node)
        else:
            default_config[key] = value
    return default_config


def get_config(*keys, default=None, config=None, override=None):
    """
    Get (recursively) a configuration value from the settings dictionary.
    Args:
        *key: A variable number of string arguments representing the keys to access the nested configuration.
        default: The default value to return if the specified key path does not exist. Defaults to None.
        config: The configuration dictionary to use. If None, the global config will be used. Defaults to None.
        override: An optional dictionary to override the default config for this lookup. Defaults to None.

    Examples:
        ```python
        get_config("llm", "model")
        get_config("llm", "non_existent_key", default="default_value")
        ```
    """
    # the config should not be changed outside
    cloned_config = copy.deepcopy(config or default_config)
    if len(keys) == 0:
        return cloned_config
    if override is not None:
        cloned_config = merge_configs(override, cloned_config)
    if len(keys) == 1:
        # if starts with @/, it's a reference to another config value
        if isinstance(keys[0], str) and keys[0].startswith("@/"):
            ref_keys = [u for u in keys[0][2:].split("/") if u]
            if len(ref_keys) == 1:
                # fetch the default variant if only the service name is given
                default_variant = cloned_config.get(ref_keys[0], {}).get(
                    "default", None
                )
                if default_variant is not None:
                    ref_keys.append(default_variant)
                else:
                    raise ValueError(
                        f"get_config: No default variant found for {ref_keys[0]}"
                    )
            return get_config(*ref_keys, default=default, config=cloned_config)
        else:
            return cloned_config.get(keys[0], default)
    else:
        current = cloned_config
        # drill down into the nested dictionary
        for k in keys:
            current = current.get(k, None)
            if current is None:
                return default
        return current


def config_exists(*keys, config=None, override=None) -> bool:
    """
    Check if a configuration key path exists in the settings dictionary.

    Args:
        *keys: A variable number of string arguments representing the keys to access the nested configuration.
        config: The configuration dictionary to use. If None, the global config will be used. Defaults to None.
        override: An optional dictionary to override the default config for this lookup. Defaults to None.
    """
    return get_config(*keys, config=config, override=override) is not None


def resolve_config(*keys, config=None, override=None) -> dict:
    """
    Resolve a configuration dictionary for a given service and its default variant.

    Args:
        *keys: A variable number of string arguments representing the keys to access the nested configuration.
        config: The configuration dictionary to use. If None, the global config will be used. Defaults to None.
        override: An optional dictionary to override the default config for this lookup. Defaults to None.
    Returns:
        dict: The resolved configuration dictionary for the specified service and its default variant.
    service_config = get_config(*keys, config=config, override=override)
    if service_config is None:
        raise ValueError(f"resolve_config: No configuration found for {keys}")
    return service_config
    """
    service_config = get_config(*keys, config=config, override=override)
    if service_config is None:
        return None
    if isinstance(service_config, str):
        if service_config.startswith("@/"):
            return resolve_reference(service_config, config=config, override=override)
        else:
            return service_config
    elif isinstance(service_config, dict):
        if "default" in service_config:
            default_variant = service_config["default"]
            if default_variant in service_config:
                service_config = service_config[default_variant]
            else:
                raise ValueError(
                    f"resolve_config: Default variant '{default_variant}' not found in configuration for {keys}"
                )

        resolved = {}
        for k, v in service_config.items():
            if isinstance(v, str) and v.startswith("@/"):
                resolved[k] = resolve_reference(v, config=config, override=override)
            elif isinstance(v, str) and v.startswith("$/"):
                resolved[k] = get_full_path(v)
            else:
                resolved[k] = v
        return resolved
    return service_config


def resolve_reference(ref: str, config=None, override=None) -> dict:
    """
    Resolves iteratively a configuration reference string in the format '@/service/variant'.
    That is, you get a JSON dictionary without any further references inside.

    Args:
        ref: The reference string to resolve (e.g., '@/llm/openai').
        config: The configuration dictionary to use. If None, the global config will be used. Defaults to None.
        override: An optional dictionary to override the default config for this lookup. Defaults to None.
    Returns:
        dict: The resolved configuration dictionary for the specified reference.
    """
    if not ref.startswith("@/"):
        raise ValueError(f"resolve_reference: Invalid reference format: {ref}")
    if ref == "@/":
        # special case to get the whole config
        if override is not None:
            found = merge_configs(override, config or default_config)
        else:
            found = config or default_config
    else:
        ref_keys = [u for u in ref[2:].split("/") if u]
        if len(ref_keys) == 1:
            # fetch the default variant if only the service name is given
            default_variant = get_config(
                ref_keys[0], "default", config=config, override=override
            )
            if default_variant is not None:
                ref_keys.append(default_variant)
            else:
                return None
        found = get_config(*ref_keys, config=config, override=override)

    # check if any of the values are itself a reference
    if isinstance(found, dict):
        resolved = {}
        for k, v in found.items():
            if isinstance(v, str) and v.startswith("@/"):
                resolved[k] = resolve_reference(v, config=config, override=override)
            elif isinstance(v, str) and v.startswith("$/"):
                resolved[k] = get_full_path(v)
            else:
                resolved[k] = v
        return resolved
    elif isinstance(found, str) and found.startswith("@/"):
        return resolve_reference(found, config=config, override=override)
    return found

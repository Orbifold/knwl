# ============================================================================================
# The settings are as much settings as recipe in the case of knwl.
# By enabling/disabling certain features here, you can change the behavior of knwl.
# ============================================================================================
import copy
import os
from typing import Optional

from knwl.utils import get_full_path

"""
Default configuration for Knwl services.
The "default" refers both to the fact that it defines defaults and the "default" space underneath the user's home directory.
That is, you have out of the box a '~/.knwl/user/default' space where all user data is stored unless otherwise specified.
If you use the `Knwl` utility class, you can specify a different space when adding or asking.
"""
_default_config = {"blob": {"default": "file_system", "file_system": {"class": "knwl.storage.file_storage.FileStorage", "base_path": "$/data/blobs", }, }, "chunking": {"default": "tiktoken", "tiktoken": {"class": "knwl.chunking.TiktokenChunking", "model": "gpt-4o-mini", "chunk_size": 1024, "chunk_overlap": 128, }, }, "chunk_store": {"default": "user", "user": {"class": "knwl.semantic.rag.chunk_store.ChunkStore", "chunker": "@/chunking/tiktoken", "chunk_embeddings": "@/vector/user_chunks", "chunk_storage": "@/json/user_chunks", }, }, "document_store": {"default": "user", "user": {"class": "knwl.semantic.rag.document_store.DocumentStore", "document_storage": "@/json/user_documents", }, },
                   "entity_extraction": {"default": "basic", "basic": {"class": "knwl.extraction.basic_entity_extraction.BasicEntityExtraction", "llm": "@/llm", }, }, "graph_extraction": {"default": "full", "full": {"class": "knwl.extraction.basic_graph_extraction.BasicGraphExtraction", "mode": "full",  # fast or full
                                                                                                                                                                                                                        "llm": "@/llm", }, "fast": {"class": "knwl.extraction.basic_graph_extraction.BasicGraphExtraction", "mode": "fast",  # fast or full
                                                                                                                                                                                                                                                    "llm": "@/llm", }, }, "glean_graph_extraction": {"default": "max3", "max3": {"class": "knwl.extraction.glean_graph_extraction.GleanGraphExtraction", "llm": "@/llm", "max_glean": 3, }, }, "graph": {"default": "user", "user": {"class": "knwl.storage.networkx_storage.NetworkXGraphStorage", "format": "graphml", "memory": False, "path": "$/user/default/graph.graphml", }, "memory": {"class": "knwl.storage.networkx_storage.NetworkXGraphStorage", "format": "graphml", "memory": True, }, },
                   "graph_rag": {"default": "user", "memory": {"class": "knwl.semantic.graph_rag.graph_rag.GraphRAG", "semantic_graph": "@/semantic_graph/memory", "ragger": "@/rag_store", "graph_extractor": "@/graph_extraction/basic", "keywords_extractor": "@/keywords_extraction", }, "user": {"class": "knwl.semantic.graph_rag.graph_rag.GraphRAG", "semantic_graph": "@/semantic_graph/user", "ragger": "@/rag_store/user", "graph_extractor": "@/graph_extraction", "keywords_extractor": "@/keywords_extraction", }, },
                   "json": {"default": "basic", "basic": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/data/data.json", }, "node_store": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/tests/graphrag/node_store.json", }, "edge_store": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/tests/graphrag/edge_store.json", }, "document_store": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/tests/graphrag/document_store.json", }, "chunk_store": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/tests/graphrag/chunk_store.json", }, "user_documents": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/user/default/documents.json", },
                            "user_chunks": {"class": "knwl.storage.json_storage.JsonStorage", "path": "$/user/default/chunks.json", }, }, "keywords_extraction": {"default": "basic", "basic": {"class": "knwl.extraction.basic_keywords_extraction.BasicKeywordsExtraction", "llm": "@/llm", }, },
                   "llm": {"default": "ollama", "ollama": {"class": "knwl.llm.ollama.OllamaClient", "model": "qwen2.5:7b", "caching_service": "@/llm_caching/user", "temperature": 0.1, "context_window": 32768, }, "ollama_gemma": {"class": "knwl.llm.ollama.OllamaClient", "model": "gemma3:27b", "caching_service": "@/llm_caching/user", "temperature": 0.1, "context_window": 32768, }, "openai": {"class": "knwl.llm.openai.OpenAIClient", "model": "gpt-4o-mini", "caching_service": "@/llm_caching/user", "temperature": 0.1, "context_window": 32768, }, "anthropic": {"class": "knwl.llm.anthropic.AnthropicClient", "model": "claude-sonnet-4-5-20250929",  # Sonnet 4.5 model
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 "caching_service": "@/llm_caching/user", "temperature": 0.1, "context_window": 4096,  # Max tokens for response (lower to avoid streaming requirement)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 "api_key": os.getenv("ANTHROPY_API_KEY", ""), }, },
                   "llm_caching": {"default": "user", "tests": {"class": "knwl.llm.json_llm_cache.JsonLLMCache", "path": "$/tests/llm.json", }, "user": {"class": "knwl.llm.json_llm_cache.JsonLLMCache", "path": "$/user/default/llm_cache.json", }, }, "logging": {"enabled": True, "level": "INFO", "path": "$/user/default/knwl.log"}, "rag_store": {"default": "user", "user": {"class": "knwl.semantic.rag.rag_store.RagStore", "document_store": "@/document_store/user", "chunk_store": "@/chunk_store/user", "chunker": "@/chunking", "auto_chunk": True, }, }, "semantic_graph": {"default": "user", "user": {"class": "knwl.semantic.graph.semantic_graph.SemanticGraph", "graph_store": "@/graph/user",  # the topology
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        "node_embeddings": "@/vector/user_nodes",  # the node embeddings
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        "edge_embeddings": "@/vector/user_edges",  # the edge embeddings
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        "summarization": "@/summarization",  # how to summarize long texts
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        }, "memory": {"class": "knwl.semantic.graph.semantic_graph.SemanticGraph", "graph_store": "@/graph/memory",  # the topology
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      "node_embeddings": "@/vector/memory",  # the node embeddings
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      "edge_embeddings": "@/vector/memory",  # the edge embeddings
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      "summarization": "@/summarization",  # how to summarize long texts
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      }, },
                   "summarization": {"default": "llm", "concat": {"class": "knwl.summarization.concat.SimpleConcatenation", "max_tokens": 500, }, "llm": {"class": "knwl.summarization.ollama.OllamaSummarization", "llm": "@/llm", "max_tokens": 150, "chunker": "@/chunking/tiktoken", }, },
                   "vector": {"default": "chroma", "chroma": {"class": "knwl.storage.chroma_storage.ChromaStorage", "memory": False, "path": "$/tests/vector", "collection_name": "default", "metadata": [], }, "user_nodes": {"class": "knwl.storage.chroma_storage.ChromaStorage", "memory": False, "path": "$/user/default/vectors", "collection_name": "nodes", }, "user_edges": {"class": "knwl.storage.chroma_storage.ChromaStorage", "memory": False, "path": "$/user/default/vectors", "collection_name": "edges", }, "user_chunks": {"class": "knwl.storage.chroma_storage.ChromaStorage", "memory": False, "path": "$/user/default/vectors", "collection_name": "chunks", }, "memory": {"class": "knwl.storage.chroma_storage.ChromaStorage", "memory": True, "collection_name": "default", },
                              "chunks": {"class": "knwl.storage.chroma_storage.ChromaStorage", "memory": True, "collection_name": "chunks", }, }, }

_active_config = copy.deepcopy(_default_config)


def set_active_config(new_config: dict):
    """
    Set a new active configuration dictionary.
    This overrides the whole default configuration and can be a better solution then overriding if too many settings need to be changed.

    Args:
        new_config (dict): The new active configuration dictionary to set.
    """
    global _active_config
    _active_config = new_config


def reset_active_config():
    """
    Reset the active configuration to the default configuration.
    """
    global _active_config
    _active_config = copy.deepcopy(_default_config)


def reset_config():
    """
    This is an alias for `reset_active_config` to reset the active configuration to the default configuration.
    """
    reset_active_config()


def merge_configs(override: dict, base_config: dict) -> dict:
    """
    Recursively merge two configuration dictionaries.

    This function merges an override configuration dictionary into a default configuration
    dictionary. For nested dictionaries, the merge is performed recursively. Non-dictionary
    values in the override will replace corresponding values in the default configuration.

    Args:
        override (dict): The configuration dictionary containing values to override defaults.
            Can be None or empty, in which case the base_config is returned unchanged.
        base_config (dict): The base configuration dictionary that will be updated with
            override values. This dictionary is modified in place.

    Returns:
        dict: The merged configuration dictionary (same object as base_config after modification).

    Raises:
        ValueError: If override is not None and not a dictionary.
        ValueError: If base_config is not None and not a dictionary.

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
        return base_config
    if not isinstance(override, dict):
        raise ValueError("merge_configs: override must be a dictionary")
    if base_config is None:
        return override
    if not isinstance(base_config, dict):
        raise ValueError("merge_configs: base_config must be a dictionary")

    for key, value in override.items():
        if isinstance(value, dict):
            # get node or create one
            node = base_config.setdefault(key, {})
            merge_configs(value, node)
        else:
            base_config[key] = value
    return base_config


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
    cloned_config = copy.deepcopy(config or _active_config)
    if len(keys) == 0:
        return cloned_config
    if override is not None:
        cloned_config = merge_configs(override, cloned_config)
    if isinstance(keys[0], str) and keys[0].startswith("@/") and len(keys) > 1:
        # ignore the other keys since things are given via reference
        return get_config(keys[0], default=default, config=cloned_config)
    if len(keys) == 1:
        # if starts with @/, it's a reference to another config value
        if isinstance(keys[0], str) and keys[0].startswith("@/"):
            ref_keys = [u for u in keys[0][2:].split("/") if u]
            if len(ref_keys) == 1:
                if ref_keys[0] not in cloned_config:
                    return default
                # fetch the default variant if only the service name is given
                default_variant = cloned_config.get(ref_keys[0], {}).get("default", None)
                if default_variant is not None:
                    ref_keys.append(default_variant)
                else:
                    raise ValueError(f"get_config: No default variant found for {ref_keys[0]}")
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


def resolve_dict(d: dict, config: dict = None) -> dict:
    """
    Resolves a configuration dictionary by handling default variants, reference strings, and nested dictionaries.

    If the dictionary contains a "default" key, replaces the dictionary with the variant specified by the "default" value.
    Recursively resolves:
    - Strings starting with "@/": treated as references and resolved via `resolve_reference`.
    - Strings starting with "$/": resolved to full paths via `get_full_path`.
    - Nested dictionaries: resolved recursively.

    Args:
        d (dict): The configuration dictionary to resolve.

    Returns:
        dict: The resolved configuration dictionary.

    Raises:
        ValueError: If the "default" variant specified is not found in the dictionary.
    """
    if "default" in d:
        default_variant = d["default"]
        if default_variant in d:
            d = d[default_variant]
        else:
            raise ValueError(f"resolve_dict: default variant '{default_variant}' not found in configuration.")

    resolved = {}
    for k, v in d.items():
        if isinstance(v, str) and v.startswith("@/"):
            resolved[k] = resolve_reference(v, config=config)
        elif isinstance(v, str) and v.startswith("$/"):
            resolved[k] = get_full_path(v)
        elif isinstance(v, dict):
            resolved[k] = resolve_dict(v, config=config)
        else:
            resolved[k] = v
    return resolved


def resolve_config(*keys, config=None, override=None) -> dict:
    """
    Resolve a configuration for a given service and its default variant.
    You can use '@/' to resolve the whole config if needed.

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
                raise ValueError(f"resolve_config: Default variant '{default_variant}' not found in configuration for {keys}")

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
            found = merge_configs(override, config or _active_config)
        else:
            found = config or _active_config
    else:
        ref_keys = [u for u in ref[2:].split("/") if u]
        if len(ref_keys) == 1:
            # fetch the default variant if only the service name is given
            default_variant = get_config(ref_keys[0], "default", config=config, override=override)
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
    if str(found).startswith("$/"):
        return get_full_path(found)
    return found


def get_active_config() -> dict:
    """
    Get a deep copy of the default configuration dictionary.

    Returns:
        dict: A deep copy of the default configuration dictionary.
    """
    return copy.deepcopy(_active_config)


def get_custom_config(namespace: str = "default", llm_provider: str = None, llm_model: str = None, override: Optional[dict] = None, ) -> dict:
    """
    Get the configuration dictionary adjusted for a specific namespace, LLM provider and LLM model.
    - If the namespace is an absolute path (starts with '/'), it will be used as is for storage paths.
    - If no LLM provider or model is given, the default ones from the active config will be used.
    - This is primarily for the Kwnl utility class to create isolated knowledge spaces, but can be used elsewhere too.

    Args:
        namespace: The knowledge space namespace. Defaults to "default". You find this directory under the user's home directory (~/) unless an absolute path is given.
        llm_provider: The LLM provider to set as default (e.g., "openai"). Defaults to None.
        llm_model: The LLM model to set for the given provider (e.g., "gpt-4o-mini"). Defaults to None.
        override: An optional dictionary to override additional configuration settings. Defaults to None.
    """
    if namespace is None or len(str(namespace).strip()) == 0:
        raise ValueError("get_custom_config: namespace cannot be empty.")

    base_config = get_active_config()
    if namespace.startswith("~/"):
        namespace = os.path.expanduser(namespace)
    if namespace.startswith("/"):  # absolute path
        os.makedirs(namespace, exist_ok=True)
        space_path = namespace
    else:
        space_path = f"$/user/{namespace}"

    # replace everywhere the $/user/default with the space path
    def replace_space_path(d):
        for k, v in d.items():
            if isinstance(v, dict):
                replace_space_path(v)
            elif isinstance(v, str) and "$/user/default" in v:
                d[k] = v.replace("$/user/default", space_path)

    # replace the LLM provider and model if given
    def replace_default_provider(d):
        llm_config = d.get("llm", {})
        if llm_provider in llm_config:
            base_config["llm"]["default"] = llm_provider
        else:
            raise ValueError(f"get_custom_config: LLM provider '{llm_provider}' not found in configuration.")

    def replace_default_model(d):
        llm_config = d.get("llm", {})
        provider_config = llm_config.get(llm_provider, {})
        if "model" in provider_config:
            provider_config["model"] = llm_model

        else:
            raise ValueError(f"get_custom_config: LLM model setting not found for provider '{llm_provider}'.")

    replace_space_path(base_config)
    if llm_provider is not None:
        replace_default_provider(base_config)
    if llm_model is not None:
        replace_default_model(base_config)
    # if additional overrides are given, apply them too
    if override is not None:
        base_config = merge_configs(override, base_config)
    return base_config


def merge_into_active_config(section: dict) -> dict:
    """
    Merges an configuration section into the active configuration.
    This a combination of `get_config`, `merge_configs` and `set_active_config`.

    Args:
        section (dict): The configuration dictionary containing values to override in the active configuration.
    """
    current_config = get_config()
    if section is None:
        return current_config
    if not isinstance(section, dict):
        raise ValueError("merge_into_active_config: section must be a dictionary")
    if len(section) == 0:
        return current_config
    new_config = merge_configs(section, current_config)
    set_active_config(new_config)
    return copy.deepcopy(new_config)

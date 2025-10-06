# ============================================================================================
# The settings are as much settings as recipe in the case of knwl.
# By enabling/disabling certain features here, you can change the behavior of knwl.
# ============================================================================================

default_config = {
    "knwl": {
        "summarization": {
            "enabled": True,
        }
    },
    "global": {},
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
    "extraction": {
        "default": "glean",
        "glean": {
            "class": "knwl.extraction.glean_extraction.GleaningExtraction",
            "llm": "glean",
            "chunker": "tiktoken",
            "temperature": 0.1,
            "max_retries": 3,
        },
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
        "glean": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "gemma3:4b",
            "caching": "json",
            "temperature": 0.1,
            "context_window": 32768,
        },
        "glean-qwen": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "qwen2.5:7b",
            "caching": "json",
            "temperature": 0.0,
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
    "logging": {"enabled": True, "level": "DEBUG", "path": "knwl.log"},
    "vector": {
        "default": "chroma",
        "chroma": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "memory": False,
            "path": "$test/vector",
            "collection": "default",
            "metadata": [],
        },
    },
    "graph": {
        "default": "nx",
        "nx": {
            "class": "knwl.storage.networkx_storage.NetworkXStorage",
            "format": "graphml",
            "memory": False,
            "path": "$test/graph.graphml",
        },
    },
    "json": {
        "default": "basic",
        "basic": {
            "class": "knwl.storage.json_storage.JsonStorage",
            "path": "$test/data.json",
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

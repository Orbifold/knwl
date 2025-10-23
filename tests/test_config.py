import pytest
from knwl.config import get_config, merge_configs


def test_config_get():
    config = {"a": {"b": {"c": 1}}}
    assert get_config("a", "b", "c", config=config) == 1
    assert get_config("a", "b", "d", default=42, config=config) == 42
    assert get_config("a", "e", default=3, config=config) == 3
    assert get_config("x", default=None, config=config) is None
    assert get_config("a", "b", config=config) == {"c": 1}
    assert get_config("a", config=config) == {"b": {"c": 1}}
    assert get_config(config=config) == config
    assert (
        get_config("nonexistent", default="default_value", config=config)
        == "default_value"
    )
    assert get_config("llm", "ollama", "model") == "qwen2.5:14b"
    assert get_config("llm", "ollama", "temperature") == 0.1
    assert get_config("llm", "ollama", "context_window") == 32768
    assert get_config("llm", "ollama", "caching_service") == "@/llm_caching/json"
    assert get_config("llm_caching", "json", "path") == "$test/llm.json"
    assert get_config("nonexistent", default="default_value") == "default_value"
    assert get_config("llm", "nonexistent", default={"key": "value"}) == {
        "key": "value"
    }
    assert get_config("storage", "documents", "nonexistent", default=123) == 123
    assert get_config("storage", "nonexistent", default={"a": 1}) == {"a": 1}
    assert get_config("nonexistent", default=None) is None
    assert (
        get_config(
            "llm",
            "ollama",
            "model",
            override={"llm": {"ollama": {"model": "custom_model:1b"}}},
        )
        == "custom_model:1b"
    )
    assert (
        get_config(
            "llm",
            "ollama",
            "temperature",
            override={"llm": {"ollama": {"temperature": 0.56}}},
        )
        == 0.56
    )
    assert get_config("@/llm/ollama/model") == "qwen2.5:14b"
    assert get_config("@/a/b", override=config) == {"c": 1}
    assert get_config("@/a/b/", override=config) == {"c": 1}


def test_config_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 20}, "e": 5}
    merged = {
        "a": 1,
        "b": {"c": 20, "d": 3},
        "e": 5,
    }

    result = merge_configs(override, base)
    assert result == merged

    result = merge_configs({}, base)
    assert result == base
    result = merge_configs(override, {})
    assert result == override
    result = merge_configs({}, {})
    assert result == {}
    result = merge_configs(None, None)
    assert result == None

    with pytest.raises(ValueError):
        merge_configs("not_a_dict", base)
    with pytest.raises(ValueError):
        merge_configs(override, "not_a_dict")

    
    config = {
        "llm": {"openai": {"caching_service": "@/llm_caching/special"}},
        "llm_caching": {"special": {"class": "A"}},
    }
    result  = get_config("llm", "openai", "caching_service", override=config)
    assert result == "@/llm_caching/special"
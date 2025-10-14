
from knwl.config import get_config


def test_config_get():
    config = {"a": {"b": {"c": 1}}}
    assert get_config("a", "b", "c", config=config) == 1
    assert get_config("a", "b", "d", default=42, config=config) == 42
    assert get_config("a", "e", default=3, config=config) == 3
    assert get_config("x", default=None, config=config) is None
    assert get_config("a", "b", config=config) == {"c": 1}
    assert get_config("a", config=config) == {"b": {"c": 1}}
    assert get_config(config=config) == config
    assert get_config("nonexistent", default="default_value", config=config) == "default_value"
    assert get_config("llm", "ollama", "model") == "qwen2.5:14b"
    assert get_config("llm", "ollama", "temperature") == 0.1
    assert get_config("llm", "ollama", "context_window") == 32768
    assert get_config("llm", "ollama", "caching") == "json"
    assert get_config("llm_caching", "json", "path") == "$test/llm.json"
    assert get_config("nonexistent", default="default_value") == "default_value"
    assert get_config("llm", "nonexistent", default={"key": "value"}) == {"key": "value"}
    assert get_config("storage", "documents", "nonexistent", default=123) == 123
    assert get_config("storage", "nonexistent", default={"a": 1}) == {"a": 1}
    assert get_config("nonexistent", default=None) is None
    assert get_config("llm", "ollama", "model", override={"llm":{"ollama":{"model": "custom_model:1b"}}}) == "custom_model:1b"
    assert get_config("llm", "ollama", "temperature", override={"llm":{"ollama":{"temperature": 0.56}}}) == 0.56
    assert get_config("@/llm/ollama/model") == "qwen2.5:14b"
    assert get_config("@/a/b", override=config) == {"c": 1}
    assert get_config("@/a/b/", override=config) == {"c": 1}



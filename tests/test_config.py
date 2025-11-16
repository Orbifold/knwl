import pytest

from knwl.config import get_config, merge_configs, reset_active_config, resolve_dict, set_active_config, merge_into_active_config
from knwl.config import resolve_reference, resolve_config, get_custom_config

pytestmark = pytest.mark.basic


def test_config_get():
    config = {"a": {"b": {"c": 1}}}
    assert get_config("a", "b", "c", config=config) == 1
    assert get_config("a", "b", "d", default=42, config=config) == 42
    assert get_config("a", "e", default=3, config=config) == 3
    assert get_config("x", default=None, config=config) is None
    assert get_config("a", "b", config=config) == {"c": 1}
    assert get_config("a", config=config) == {"b": {"c": 1}}
    assert get_config(config=config) == config
    assert (get_config("nonexistent", default="default_value", config=config) == "default_value")
    assert get_config("llm", "ollama", "model") == "qwen2.5:7b"
    assert get_config("llm", "ollama", "temperature") == 0.1
    assert get_config("llm", "ollama", "context_window") == 32768
    assert get_config("llm", "ollama", "caching_service") == "@/llm_caching/user"
    assert get_config("llm_caching", "user", "path") == "$/user/default/llm_cache.json"
    assert get_config("nonexistent", default="default_value") == "default_value"
    assert get_config("llm", "nonexistent", default={"key": "value"}) == {"key": "value"}
    assert get_config("storage", "documents", "nonexistent", default=123) == 123
    assert get_config("storage", "nonexistent", default={"a": 1}) == {"a": 1}
    assert get_config("nonexistent", default=None) is None
    assert (get_config("llm", "ollama", "model", override={"llm": {"ollama": {"model": "custom_model:1b"}}}, ) == "custom_model:1b")
    assert (get_config("llm", "ollama", "temperature", override={"llm": {"ollama": {"temperature": 0.56}}}, ) == 0.56)
    assert get_config("@/llm/ollama/model") == "qwen2.5:7b"
    assert get_config("@/a/b", override=config) == {"c": 1}
    assert get_config("@/a/b/", override=config) == {"c": 1}
    # should fetch the default if the reference is only the service name
    assert "class" in get_config("@/rag_store")


def test_config_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 20}, "e": 5}
    merged = {"a": 1, "b": {"c": 20, "d": 3}, "e": 5, }

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

    config = {"llm": {"openai": {"caching_service": "@/llm_caching/special"}}, "llm_caching": {"special": {"class": "A"}}, }
    result = get_config("llm", "openai", "caching_service", override=config)
    assert result == "@/llm_caching/special"


def test_resolve_reference():
    config = {"klm": {"default": "a", "a": {"u": 4, "v": 5, "w": 6}}, "abc": {"default": "b", "b": {"z": "@/klm"}, "c": {"y": "@/klm/a/u"}}, }
    result = resolve_reference("@/abc/b/z", override=config)
    assert result == {"u": 4, "v": 5, "w": 6}

    result = resolve_reference("@/abc/c/y", override=config)
    assert result == 4

    result = resolve_reference("@/klm", override=config)
    assert result == {"u": 4, "v": 5, "w": 6}

    result = resolve_reference("@/abc/c", override=config)
    assert result == {"y": 4}


def test_resolve_config():
    config = {"klm": {"default": "a", "a": {"u": 4, "v": 5, "w": 6}}, "abc": {"default": "b", "b": {"z": "@/klm"}, "c": {"y": "@/klm/a/u"}}, }
    result = resolve_config("abc", override=config)
    assert result == {"z": {"u": 4, "v": 5, "w": 6}}

    result = resolve_config("klm", override=config)
    assert result == {"u": 4, "v": 5, "w": 6}

    result = resolve_config("@/abc/c", override=config)
    assert result == {"y": 4}


def test_resolve_dict():
    d = {"a": {"default": "u", "u": {"k": 4}}}
    r = resolve_dict(d)
    assert r == {"a": {"k": 4}}

    d = {"a": {"default": "u", "u": {"k": "$/user/r"}}}
    r = resolve_dict(d)
    assert ".knwl" in r["a"]["k"]

    d = {"a": {"default": "u", "u": {"k": "@/b"}}, "b": {"default": "data", "data": {"d": 56}}, }
    r = resolve_dict(d, d)
    assert r["a"] == {"k": {"d": 56}}
    assert r["b"] == {"d": 56}


def test_active_config():
    dumb = {"a": 6}
    set_active_config(dumb)
    assert get_config("a") == 6
    assert get_config("@/llm") is None
    assert get_config("nonexistent", default=10) == 10
    assert get_config("a", override={"a": 12}) == 12
    reset_active_config()
    assert get_config("@/llm") is not None


def test_get_custom_config_namespace():
    # Test with default namespace
    config = get_custom_config(namespace="default")
    assert "$/user/default" in config["json"]["user_documents"]["path"]

    # Test with custom namespace
    config = get_custom_config(namespace="custom_space")
    assert "$/user/custom_space" in config["json"]["user_documents"]["path"]
    assert "$/user/custom_space" in config["json"]["user_chunks"]["path"]
    assert "$/user/custom_space" in config["graph"]["user"]["path"]
    assert "$/user/custom_space" in config["llm_caching"]["user"]["path"]

    # Test that original config is not modified
    original = get_config("json", "user_documents", "path")
    assert "$/user/default" in original


def test_get_custom_config_absolute_path(tmp_path):
    # Test with absolute path
    abs_path = str(tmp_path / "test_space")
    config = get_custom_config(namespace=abs_path)

    assert abs_path in config["json"]["user_documents"]["path"]
    assert abs_path in config["llm_caching"]["user"]["path"]
    assert abs_path in config["graph"]["user"]["path"]


def test_get_custom_config_llm_provider():
    # Test with LLM provider change
    config = get_custom_config(namespace="test", llm_provider="openai")
    assert config["llm"]["default"] == "openai"

    # Test with invalid provider
    with pytest.raises(ValueError, match="LLM provider.*not found"):
        get_custom_config(namespace="test", llm_provider="nonexistent")


def test_get_custom_config_llm_model():
    # Test with LLM model change
    config = get_custom_config(namespace="test", llm_provider="ollama", llm_model="custom:7b")
    assert config["llm"]["ollama"]["model"] == "custom:7b"

    # Test model change with openai
    config = get_custom_config(namespace="test", llm_provider="openai", llm_model="gpt-4")
    assert config["llm"]["openai"]["model"] == "gpt-4"


def test_get_custom_config_combined():
    # Test namespace + provider + model
    config = get_custom_config(namespace="myspace", llm_provider="anthropic", llm_model="claude-3")
    assert "$/user/myspace" in config["json"]["user_chunks"]["path"]
    assert config["llm"]["default"] == "anthropic"
    assert config["llm"]["anthropic"]["model"] == "claude-3"


def test_get_custom_config_empty_namespace():
    with pytest.raises(ValueError, match="namespace cannot be empty"):
        get_custom_config(namespace="")

    with pytest.raises(ValueError, match="namespace cannot be empty"):
        get_custom_config(namespace="   ")

    with pytest.raises(ValueError, match="namespace cannot be empty"):
        get_custom_config(namespace=None)


def test_get_custom_config_isolation():
    # Verify config isolation - changes don't affect active config
    original_default = get_config("llm", "default")

    config1 = get_custom_config(namespace="space1", llm_provider="openai")
    config2 = get_custom_config(namespace="space2", llm_provider="anthropic")

    assert config1["llm"]["default"] == "openai"
    assert config2["llm"]["default"] == "anthropic"
    assert get_config("llm", "default") == original_default


def test_extra():
    # Test with extra overrides
    extra = {"logging": {"enabled": False, "level": "ERROR", "path": "$/user/extra/knwl.log"}}
    config = get_custom_config(namespace="extra_space", override=extra)
    assert config["logging"]["enabled"] is False
    assert config["logging"]["level"] == "ERROR"
    assert "$/user/extra/knwl.log" in config["logging"]["path"]


def test_merge_into_active_config():
    reset_active_config()
    base_value = get_config("llm", "ollama", "temperature")
    override = {"llm": {"ollama": {"temperature": 0.75}}}
    merge_into_active_config(override)
    new_value = get_config("llm", "ollama", "temperature")
    assert new_value == 0.75

    found = get_config("a", "b")
    assert found is None
    merge_into_active_config({"a": {"b": 42}})
    found = get_config("a", "b")
    assert found == 42

    reset_active_config()
    assert get_config("a", "b") is None
    assert get_config("llm", "ollama", "temperature") == base_value
    with pytest.raises(ValueError):
        merge_into_active_config("not_a_dict")

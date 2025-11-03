import pytest

from knwl.llm.json_llm_cache import JsonLLMCache
from knwl.models import KnwlAnswer
pytestmark = pytest.mark.basic
cache = JsonLLMCache()


@pytest.mark.asyncio
async def test_llm_cache():
    d = {
        "messages": [{"role": "user", "content": "hello"}],
        "llm_model": "qwen2.5:14b",
        "llm_service": "ollama",
        "answer": "world",
        "timing": 20.0,
    }
    a = KnwlAnswer(**d)
    id = await cache.upsert(a)
    assert await cache.is_in_cache(
        **{
            "messages": [{"role": "user", "content": "hello"}],
            "llm_model": "qwen2.5:14b",
            "llm_service": "ollama",
        }
    )
    cached_item = await cache.get_by_id(id)
    assert cached_item.from_cache
    assert cached_item.messages == [{"role": "user", "content": "hello"}]
    assert await cache.is_in_cache("hello", "ollama", "qwen2.5:14b")
    assert not await cache.is_in_cache("hello again", "ollama", "qwen2.5:14b")
    assert not await cache.is_in_cache("hello", "ollama", "another_model")
    await cache.delete(a)
    assert not await cache.is_in_cache("hello", "ollama", "qwen2.5:14b")
    with pytest.raises(ValueError):
        await cache.upsert(None)
    with pytest.raises(ValueError):
        await cache.upsert("not a KnwlAnswer")

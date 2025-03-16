import pytest

from knwl.llm_cache import LLMCache
from knwl.models import KnwlLLMAnswer

cache = LLMCache("testing", True)


@pytest.mark.asyncio
async def test_llm_cache():
    d = {
        "messages": [{"role": "user", "content": "hello"}],
        "llm_model": "qwen2.5:14b",
        "llm_service": "ollama",
        "answer": "world",
        "total_time": 20.0
    }
    a = KnwlLLMAnswer(**d)
    id = await cache.upsert(a)
    assert await cache.is_in_cache(**{
        "messages": [{"role": "user", "content": "hello"}],
        "llm_model": "qwen2.5:14b",
        "llm_service": "ollama"})
    cached_item = await cache.get_by_id(id)
    assert cached_item.from_cache
    assert cached_item.messages == [{"role": "user", "content": "hello"}]
    assert await cache.is_in_cache("hello", "ollama", "qwen2.5:14b")
    assert not await cache.is_in_cache("hello again", "ollama", "qwen2.5:14b")
    assert not await cache.is_in_cache("hello", "ollama", "another_model")
    await cache.delete(a)
    assert not await cache.is_in_cache("hello", "ollama", "qwen2.5:14b")

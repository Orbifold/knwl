import pytest

from knwl import llm
from knwl.llm.ollama import OllamaClient
from knwl.models.KnwlLLMAnswer import KnwlLLMAnswer


@pytest.mark.asyncio
async def test_basic_ask():
    llm = OllamaClient()
    assert llm.model == "qwen2.5:14b"
    assert llm.temperature == 0.1

    llm = OllamaClient(model="gemma3:4b", temperature=0.5)
    assert llm.model == "gemma3:4b"
    assert llm.temperature == 0.5

    resp = await llm.ask("Hello")
    assert resp is not None
    assert isinstance(resp, KnwlLLMAnswer)

    assert await llm.is_cached("Hello") is True
    print("")
    print(resp.answer)

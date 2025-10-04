from unittest.mock import AsyncMock, patch

import pytest

from knwl.llm import llm, LLMClient
from knwl.models import KnwlLLMAnswer
from knwl.config import config


@pytest.mark.asyncio
async def test_history():
    prompt = "Hello"
    system_prompt = "System"
    history_messages = [
        {"role": "user", "content": "Hi"},
        {"role": "system", "content": "Hello"},
        {"role": "user", "content": "How are you?"}
    ]
    messages = LLMClient.assemble_messages(prompt, system_prompt, history_messages)
    api_response = KnwlLLMAnswer(answer="LLM answer", messages=messages, llm_model=config.llm_model, llm_service=config.llm_service)

    with patch("knwl.llm.llm.cache.storage.get_by_id", new=AsyncMock(return_value=None)) as mock_get_by_id:
        with patch("knwl.llm.llm.cache.upsert", new=AsyncMock()) as mock_upsert:
            with patch("knwl.llm.llm.cache.save", new=AsyncMock()) as mock_save:
                with patch("knwl.llm.llm.client.ask", new=AsyncMock(return_value=api_response)) as mock_chat:
                    with patch("knwl.llm.hash_args", return_value=api_response.id):
                        r = await llm.ask(prompt, system_prompt, history_messages, save=False)
                        response = r.answer
                        mock_get_by_id.assert_called_once_with(api_response.id)
                        # mock_chat.assert_called_once()
                        mock_upsert.assert_not_called()
                        mock_save.assert_not_called()
                        assert response == api_response.answer


@pytest.mark.asyncio
async def test_is_in_cache_hit():
    messages = [{"role": "user", "content": "Hi"}]
    cached_response = KnwlLLMAnswer(answer="Cached response", messages=messages, llm_model=config.llm_model, llm_service=config.llm_service)

    with patch("knwl.llm.llm.cache.get_by_id", return_value=cached_response.id) as mock_get_by_id:
        result = await llm.is_cached(messages)
        mock_get_by_id.assert_called_once_with(cached_response.id)
        assert result is True

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from knwl.llm import ollama_chat, is_in_cache


@pytest.mark.asyncio
async def test_ollama_chat_cache_hit():
    prompt = "Hello"
    system_prompt = "System"
    history_messages = [{"role": "user", "content": "Hi"}]
    key = "hashed_key"
    cached_response = {"content": "Cached response"}

    with patch("knwl.llm.ollama_cache.get_by_id", new=AsyncMock(return_value=cached_response)) as mock_get_by_id:
        with patch("knwl.llm.hash_args", return_value=key):
            response = await ollama_chat(prompt, system_prompt, history_messages)
            mock_get_by_id.assert_called_once_with(key)
            assert response == cached_response["content"]


@pytest.mark.asyncio
async def test_ollama_chat_cache_miss():
    prompt = "Hello"
    system_prompt = "System"
    history_messages = [{"role": "user", "content": "Hi"}]
    key = "hashed_key"
    api_response = {"message": {"content": "API response"}}

    with patch("knwl.llm.ollama_cache.get_by_id", new=AsyncMock(return_value=None)) as mock_get_by_id:
        with patch("knwl.llm.ollama_cache.upsert", new=AsyncMock()) as mock_upsert:
            with patch("knwl.llm.ollama_cache.save", new=AsyncMock()) as mock_save:
                with patch("knwl.llm.ollama.AsyncClient.chat", new=AsyncMock(return_value=api_response)) as mock_chat:
                    with patch("knwl.llm.hash_args", return_value=key):
                        response = await ollama_chat(prompt, system_prompt, history_messages)
                        mock_get_by_id.assert_called_once_with(key)
                        mock_chat.assert_called_once()
                        mock_upsert.assert_called_once()
                        mock_save.assert_called()
                        assert response == api_response["message"]["content"]


@pytest.mark.asyncio
async def test_ollama_chat_save_argument_true():
    prompt = "Hello"
    system_prompt = "System"
    history_messages = [
        {"role": "user", "content": "Hi"}]
    key = "hashed_key"
    api_response = {"message": {
        "content": "API response"}}

    with patch("knwl.llm.ollama_cache.get_by_id", new=AsyncMock(return_value=None)) as mock_get_by_id:
        with patch("knwl.llm.ollama_cache.upsert", new=AsyncMock()) as mock_upsert:
            with patch("knwl.llm.ollama_cache.save", new=AsyncMock()) as mock_save:
                with patch("knwl.llm.ollama.AsyncClient.chat", new=AsyncMock(return_value=api_response)) as mock_chat:
                    with patch("knwl.llm.hash_args", return_value=key):
                        response = await ollama_chat(prompt, system_prompt, history_messages, save=True)
                        mock_get_by_id.assert_called_once_with(
                            key)
                        mock_chat.assert_called_once()
                        mock_upsert.assert_called_once()
                        mock_save.assert_called_once()
                        assert response == api_response["message"]["content"]


@pytest.mark.asyncio
async def test_history():
    prompt = "Hello"
    system_prompt = "System"
    history_messages = [
        {"role": "user", "content": "Hi"},
        {"role": "system", "content": "Hello"},
        {"role": "user", "content": "How are you?"}
    ]
    key = "hashed_key"
    api_response = {"message": {
        "content": "API response"}}

    with patch("knwl.llm.ollama_cache.get_by_id", new=AsyncMock(return_value=None)) as mock_get_by_id:
        with patch("knwl.llm.ollama_cache.upsert", new=AsyncMock()) as mock_upsert:
            with patch("knwl.llm.ollama_cache.save", new=AsyncMock()) as mock_save:
                with patch("knwl.llm.ollama.AsyncClient.chat", new=AsyncMock(return_value=api_response)) as mock_chat:
                    with patch("knwl.llm.hash_args", return_value=key):
                        response = await ollama_chat(prompt, system_prompt, history_messages, save=False)
                        mock_get_by_id.assert_called_once_with(key)
                        mock_chat.assert_called_once()
                        mock_upsert.assert_called_once()
                        mock_save.assert_called_once()
                        assert response == api_response["message"]["content"]


@pytest.mark.asyncio
async def test_is_in_cache_hit():
    messages = ["Hello"]
    key = "hashed_key"
    cached_response = {"content": "Cached response"}

    with patch("knwl.llm.ollama_cache.get_by_id", new=AsyncMock(return_value=cached_response)) as mock_get_by_id:
        with patch("knwl.llm.hash_args", return_value=key):
            result = await is_in_cache(messages)
            mock_get_by_id.assert_called_once_with(key)
            assert result is True


@pytest.mark.asyncio
async def test_is_in_cache_miss():
    messages = ["Hello"]
    key = "hashed_key"

    with patch("knwl.llm.ollama_cache.get_by_id", new=AsyncMock(return_value=None)) as mock_get_by_id:
        with patch("knwl.llm.hash_args", return_value=key):
            result = await is_in_cache(messages)
            mock_get_by_id.assert_called_once_with(key)
            assert result is False

import time
from typing import List
from knwl.llm.llm_cache_base import LLMCacheBase
import ollama

from knwl.llm.llm_base import LLMBase
from knwl.models import KnwlLLMAnswer
from knwl.di import service, inject_config


@inject_config(
    {
        "llm.ollama.model": "model",
        "llm.ollama.temperature": "temperature",
        "llm.ollama.context_window": "context_window",
    }
)
@service("llm_caching", "json", param_name="caching_service")
class OllamaClient(LLMBase):
    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        context_window: int = None,
        caching_service: LLMCacheBase = None,
    ):
        super().__init__()
        self.client = (
            ollama.Client()
        )  # the AsyncClient has issues with parallel unit tests and switching models

        self._model = model
        self._temperature = temperature
        self._context_window = context_window
        self._caching_service = caching_service

    async def ask(
        self,
        question: str,
        system_message: str = None,
        extra_messages: list[dict] = None,
        key: str = None,
        category: str = None,
    ) -> KnwlLLMAnswer:
        messages = self.assemble_messages(question, system_message, extra_messages)
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        # Check cache first
        if self._caching_service is not None:
            cached = await self._caching_service.get(messages, "ollama", self._model)
            if cached is not None:
                return cached
        start_time = time.time()
        response = self.client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": self._temperature, "num_ctx": self._context_window},
        )
        end_time = time.time()
        content = response["message"]["content"]
        answer = KnwlLLMAnswer(
            answer=content,
            messages=messages,
            timing=round(end_time - start_time, 2),
            llm_model=self._model,
            llm_service="ollama",
            key=key if key else question,
            category=category if category else "none",
        )
        if self._caching_service is not None:
            await self._caching_service.upsert(answer)
        return answer

    async def is_cached(self, messages: str | List[str] | List[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self._caching_service.is_in_cache(messages, "ollama", self._model)

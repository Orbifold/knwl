import time
from typing import List
from knwl.llm.llm_cache_base import LLMCacheBase
import ollama

from knwl.llm.llm_base import LLMBase
from knwl.models import KnwlAnswer
from knwl.di import service, inject_config, defaults
from knwl.logging import log


@defaults("@/llm/ollama")
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

        self._caching_service: LLMCacheBase = caching_service
        self.validate_params()

    def validate_params(self):
        if not self.caching_service:
            log.warn("OllamaClient: No caching service provided, caching disabled.")
        if (
            not isinstance(self.caching_service, LLMCacheBase)
            and self.caching_service is not None
        ):
            raise ValueError(
                f"OllamaClient: caching_service must be an instance of LLMCacheBase, got {type(self.caching_service)}"
            )

    @property
    def model(self):
        return self._model

    @property
    def temperature(self):
        return self._temperature

    @property
    def context_window(self):
        return self._context_window

    @property
    def caching_service(self):
        return self._caching_service

    async def ask(
        self,
        question: str,
        system_message: str = None,
        extra_messages: list[dict] = None,
        key: str = None,
        category: str = None,
    ) -> KnwlAnswer:
        if not question:
            log.warn("OllamaClient: ask called with empty question.")
            return None
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
        answer = KnwlAnswer(
            question=question,
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

    async def is_cached(self, messages: str | list[str] | list[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self._caching_service.is_in_cache(messages, "ollama", self._model)

    def __repr__(self):
        return f"<OllamaClient, model={self._model}, temperature={self._temperature},  caching_service={self._caching_service}>"

    def __str__(self):
        return self.__repr__()

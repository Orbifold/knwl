import time
from typing import List
import os

import openai
from knwl.di import defaults
from knwl.llm import LLMBase, LLMCacheBase
from knwl.logging import log
from knwl.models import KnwlLLMAnswer
 
@defaults("llm", "openai")
class OpenAIClient(LLMBase):
    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        context_window: int = None,
        caching_service: LLMCacheBase = None,
    ):
        super().__init__()
        self._client = None
        self._model = model
        self._temperature = temperature
        self._context_window = context_window
        if not caching_service:
            log.warn("OpenaiClient: No caching service provided, caching disabled.")
        self._caching_service = caching_service

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:            
                self._client = openai.AsyncClient()
            except openai.OpenAIError as e:
                if "OPENAI_API_KEY" in str(e):
                    log.error(
                        "OpenAIClient: OPENAI_API_KEY environment variable not set. Please set it to use OpenAI."
                    )
                raise e
        return self._client

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
    ) -> KnwlLLMAnswer:
        messages = self.assemble_messages(question, system_message, extra_messages)
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        # Check cache first
        if self.caching_service is not None:
            cached = await self.caching_service.get(messages, "ollama", self.model)
            if cached is not None:
                return cached
        start_time = time.time()
        found = await self.client.chat.completions.create(
            messages=messages, model=self.model
        )
        end_time = time.time()
        content = found.choices[0].message.content
        answer = KnwlLLMAnswer(
            answer=content,
            messages=messages,
            timing=round(end_time - start_time, 2),
            llm_model=self.model,
            llm_service="openai",
            key=key if key else question,
            category=category if category else "none",
        )
        if self.caching_service is not None:
            await self.caching_service.upsert(answer)
        return answer

    async def is_cached(self, messages: str | List[str] | List[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self.caching_service.is_in_cache(messages, "openai", self.model)

    def __repr__(self):
        return f"<OpenAIClient, model={self.model}, temperature={self.temperature},  caching_service={self.caching_service}>"

    def __str__(self):
        return self.__repr__()

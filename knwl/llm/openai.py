import time
from typing import List

import openai

from knwl.llm.llm_base import LLMBase
from knwl.models import KnwlLLMAnswer


class OpenAIClient(LLMBase):
    def __init__(self, *args, **kwargs):
        self.client = openai.AsyncClient()
        config = kwargs.get("override", None)

        self.model = self.get_param(["llm", "openai", "model"], args, kwargs, default="gpt-4o-mini", override=config)
        self.caching_service_name = self.get_param(["llm", "ollama", "caching"], args, kwargs, False, config)
        self.caching_service = self.get_caching_service(self.caching_service_name, override=config)

    async def ask(self, messages: List[dict] | str) -> KnwlLLMAnswer:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        # Check cache first
        if self.caching_service is not None:
            cached = await self.caching_service.get(messages, "ollama", self.model)
            if cached is not None:
                return cached
        start_time = time.time()
        found = await self.client.chat.completions.create(messages=messages, model=self.model)
        end_time = time.time()
        content = found.choices[0].message.content
        return KnwlLLMAnswer(answer=content, messages=messages, timing=round(end_time - start_time, 2), llm_model=self.model, llm_service="openai")

    async def is_cached(self, messages: str | List[str] | List[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self.caching_service.is_in_cache(messages, "openai", self.model)

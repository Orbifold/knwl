import time
from typing import List

import ollama

from knwl.llm.llm_base import LLMBase
from knwl.models import KnwlLLMAnswer


class OllamaClient(LLMBase):
    def __init__(self, *args, **kwargs):
        self.client = ollama.AsyncClient()
        config = kwargs.get("override", None)

        self.model = self.get_param(["llm", "ollama", "model"], args, kwargs, default="qwen2.5:14b", override=config)
        self.temperature = self.get_param(["llm", "ollama", "temperature"], args, kwargs, 0.1, config)
        self.context_window = self.get_param(["llm", "ollama", "context_window"], args, kwargs, 32768, config)
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
        response = await self.client.chat(model=self.model, messages=messages, options={"temperature": self.temperature, "num_ctx": self.context_window}, )
        end_time = time.time()
        content = response["message"]["content"]
        answer = KnwlLLMAnswer(answer=content, messages=messages, timing=round(end_time - start_time, 2), llm_model=self.model, llm_service="ollama", )
        if self.caching_service is not None:
            await self.caching_service.upsert(answer)
        return answer

    async def is_cached(self, messages: str | List[str] | List[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self.caching_service.is_in_cache(messages, "ollama", self.model)

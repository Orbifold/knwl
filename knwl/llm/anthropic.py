import time
from typing import Optional
from anthropic import AsyncAnthropic

from knwl.di import defaults
from knwl.llm.llm_base import LLMBase
from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.logging import log
from knwl.models.KnwlAnswer import KnwlAnswer


@defaults("llm", "anthropic")
class AnthropicClient(LLMBase):
    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        context_window: int = None,
        caching_service: LLMCacheBase = None,
        api_key: Optional[str] = None,
    ):
        super().__init__()
        self._client = None
        self._model = model
        self._temperature = temperature
        self._context_window = context_window
        if not caching_service:
            log.warn("AnthropicClient: no caching service provided, caching disabled.")
        self._caching_service = caching_service
        self._api_key = api_key

    @property
    def client(self):
        """Lazy initialization of Anthropic client"""
        if self._client is None:
            try:
                if self._api_key:
                    self._client = AsyncAnthropic(api_key=self._api_key)
                else:
                    # will use ANTHROPIC_API_KEY from environment if available
                    self._client = AsyncAnthropic()
            except Exception as e:
                if "api_key" in str(e).lower():
                    log.error(
                        "AnthropicClient: ANTHROPIC_API_KEY environment variable not set. Please set it to use Anthropic."
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
    ) -> KnwlAnswer:
        messages = self.assemble_messages(question, system_message, extra_messages)
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        # Check cache first
        if self.caching_service is not None:
            cached = await self.caching_service.get(messages, "anthropic", self.model)
            if cached is not None:
                return cached
        start_time = time.time()
        response = await self.client.messages.create(
            messages=messages, 
            model=self.model,
            max_tokens=self.context_window,
            temperature=self.temperature,
        )
        end_time = time.time()
        content = response.content[0].text
        answer = KnwlAnswer(
            answer=content,
            messages=messages,
            timing=round(end_time - start_time, 2),
            llm_model=self.model,
            llm_service="anthropic",
            key=key if key else question,
            category=category if category else "none",
        )
        if self.caching_service is not None:
            await self.caching_service.upsert(answer)
        return answer

    async def is_cached(self, messages: str | list[str] | list[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self.caching_service.is_in_cache(messages, "anthropic", self.model)

    def __repr__(self):
        return f"<AnthropicClient, model={self.model}, temperature={self.temperature},  caching_service={self.caching_service}>"

    def __str__(self):
        return self.__repr__()

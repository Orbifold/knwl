from abc import abstractmethod
from typing import List

from knwl.framework_base import FrameworkBase
from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.models.KnwlLLMAnswer import KnwlLLMAnswer
from knwl.services import services


class LLMBase(FrameworkBase):

    @abstractmethod
    async def ask(
        self,
        question: str,
        system_message: str = None,
        extra_messages: list[dict] = None,
        key: str = None,
        category: str = None,
    ) -> KnwlLLMAnswer:
        pass

    @abstractmethod
    async def is_cached(self, messages: str | List[str] | List[dict]) -> bool:
        pass

    def get_caching_service(
        self, caching_service_name, override=None
    ) -> LLMCacheBase | None:

        if caching_service_name is None or caching_service_name is False:
            return None
        if isinstance(caching_service_name, LLMCacheBase):
            return caching_service_name
        if isinstance(caching_service_name, str):
            return services.instantiate_service(
                "llm_caching", caching_service_name, override=override
            )
        # Default to no caching
        return None

    @staticmethod
    def assemble_messages(
        user_message: str, system_message=None, extra_messages=None
    ) -> List[dict]:
        if user_message is None or user_message.strip() == "":
            raise ValueError("user_message cannot be None or empty.")
        if extra_messages is None:
            extra_messages = []
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.extend(extra_messages)
        messages.append({"role": "user", "content": user_message})
        return messages

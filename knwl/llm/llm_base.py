from abc import abstractmethod
from typing import List
from knwl.config import get_config
from knwl.framework_base import FrameworkBase
from knwl.llm.json_llm_cache import JsonLLMCache
from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.models.KnwlLLMAnswer import KnwlLLMAnswer
from knwl.services import services


class LLMBase(FrameworkBase):

    @abstractmethod
    async def ask(self, messages: List[dict]|str) -> KnwlLLMAnswer:
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

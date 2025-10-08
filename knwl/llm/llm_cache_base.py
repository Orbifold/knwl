from abc import ABC, abstractmethod
from typing import List

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlLLMAnswer


class LLMCacheBase(FrameworkBase):
    """
    Abstract base class for LLM caching functionality.
    """

    @abstractmethod
    async def is_in_cache(self, messages: str | List[str] | List[dict], llm_service: str, llm_model: str) -> bool:
        """Check if the given messages are cached for the specified LLM service and model."""
        pass

    @abstractmethod
    async def get(self, messages: str | List[str | List[dict]], llm_service: str, llm_model: str) -> KnwlLLMAnswer | None:
        """Retrieve cached LLM answer for the given messages, service, and model."""
        pass

    @abstractmethod
    async def get_all_ids(self) -> list[str]:
        """Get all cached item IDs."""
        pass

    @abstractmethod
    async def save(self):
        """Save the cache to persistent storage."""
        pass

    @abstractmethod
    async def clear_cache(self):
        """Clear all cached items."""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> KnwlLLMAnswer | None:
        """Retrieve cached item by its ID."""
        pass

    @abstractmethod
    async def get_by_ids(self, ids: List[str], fields=None):
        """Retrieve multiple cached items by their IDs."""
        pass

    @abstractmethod
    async def filter_new_ids(self, data: list[str]) -> set[str]:
        """Filter out IDs that are already cached."""
        pass

    @abstractmethod
    async def upsert(self, a: KnwlLLMAnswer) -> str:
        """Insert or update a cached LLM answer."""
        pass

    @abstractmethod
    async def delete_by_id(self, id: str):
        """Delete cached item by its ID."""
        pass

    @abstractmethod
    async def delete(self, a: KnwlLLMAnswer):
        """Delete cached LLM answer."""
        pass

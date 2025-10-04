from dataclasses import asdict
from typing import List

from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.models import KnwlLLMAnswer
from knwl.storage.json_storage import JsonStorage


class JsonLLMCache(LLMCacheBase):
    """
    A thin wrapper around a JSON storage object to provide caching functionality for LLM.
    """

    def __init__(self, *args, **kwargs):
        config = kwargs.get("override", None)
        self.path = self.get_param(["llm_caching", "json", "path"], args, kwargs, default="llm_cache.json", override=config)
        self.enabled = self.get_param(["llm_caching", "json", "enabled"], args, kwargs, default=True, override=config)

        self.storage = JsonStorage(path=self.path, enabled=self.enabled)

    async def is_in_cache(self, messages: str | List[str] | List[dict], llm_service: str, llm_model: str) -> bool:
        found = await self.get(messages, llm_service, llm_model)
        return found is not None

    async def get(self, messages: str | List[str | List[dict]], llm_service: str, llm_model: str) -> KnwlLLMAnswer | None:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        if isinstance(messages, list):
            messages = [{"role": "user", "content": m} if isinstance(m, str) else m for m in messages]
        if not messages or len(messages) == 0:
            return None
        key = KnwlLLMAnswer.hash_keys(messages, llm_service, llm_model)
        return await self.get_by_id(key)

    async def get_all_ids(self) -> list[str]:
        return await self.storage.get_all_ids()

    async def save(self):
        await self.storage.save()

    async def clear_cache(self):
        await self.storage.clear_cache()

    async def get_by_id(self, id: str):
        d = await self.storage.get_by_id(id)
        if d is None:
            return None
        return KnwlLLMAnswer(**d)

    async def get_by_ids(self, ids, fields=None):
        return await self.storage.get_by_ids(ids, fields=fields)

    async def filter_new_ids(self, data: list[str]) -> set[str]:
        return await self.storage.filter_new_ids(data)

    async def upsert(self, a: KnwlLLMAnswer):
        if a is None:
            raise ValueError("Cannot upsert None in LLMCache.")
        data = asdict(a)
        data["from_cache"] = True
        blob = {}
        blob[a.id] = data
        await self.storage.upsert(blob)
        return a.id

    async def delete_by_id(self, id):
        await self.storage.delete_by_id(id)

    async def delete(self, a: KnwlLLMAnswer):
        await self.storage.delete_by_id(a.id)

from typing import List

from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.models import KnwlAnswer
from knwl.storage.json_storage import JsonStorage
from knwl.di import defaults


@defaults("llm_caching", "user")
class JsonLLMCache(LLMCacheBase):
    """
    A thin wrapper around a JSON storage object to provide caching functionality for LLM.
    """

    def __init__(self, path: str = None, enabled: bool = True):
        super().__init__()
        self._path = path
        self.enabled = enabled
        if path is None:
            self.enabled = False

        self.storage = JsonStorage(path=self._path, enabled=self.enabled)

    @property
    def path(self):
        if self.storage is None:
            return None
        return self.storage.path

    async def is_in_cache(
        self, messages: str | list[str] | list[dict], llm_service: str, llm_model: str
    ) -> bool:
        found = await self.get(messages, llm_service, llm_model)
        return found is not None

    async def get(
        self, messages: str | list[str | list[dict]], llm_service: str, llm_model: str
    ) -> KnwlAnswer | None:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        if isinstance(messages, list):
            messages = [
                {"role": "user", "content": m} if isinstance(m, str) else m
                for m in messages
            ]
        if not messages or len(messages) == 0:
            return None
        key = KnwlAnswer.hash_keys(messages, llm_service, llm_model)
        return await self.get_by_id(key)

    async def get_all_ids(self) -> list[str]:
        return await self.storage.get_all_ids()

    async def save(self):
        if self.enabled:
            await self.storage.save()

    async def clear_cache(self):
        await self.storage.clear_cache()

    async def get_by_id(self, id: str):
        d = await self.storage.get_by_id(id)
        if d is None:
            return None
        return KnwlAnswer(**d)

    async def get_by_ids(self, ids, fields=None):
        return await self.storage.get_by_ids(ids, fields=fields)

    async def filter_new_ids(self, data: list[str]) -> set[str]:
        return await self.storage.filter_new_ids(data)

    async def upsert(self, a: KnwlAnswer):
        if a is None:
            raise ValueError("JsonLLMCache: cannot upsert None in LLMCache.")
        if not isinstance(a, KnwlAnswer):
            raise ValueError("JsonLLMCache: can only upsert KnwlAnswer instances in LLMCache.")
        data = a.model_dump(mode="json")
        data["from_cache"] = True
        blob = {}
        blob[a.id] = data
        await self.storage.upsert(blob)
        await self.save()
        return a.id

    async def delete_by_id(self, id):
        await self.storage.delete_by_id(id)
        await self.save()

    async def delete(self, a: KnwlAnswer):
        await self.storage.delete_by_id(a.id)
        await self.save()

    def __repr__(self):
        return f"<JsonLLMCache, path={self._path}, enabled={self.enabled}>"

    def __str__(self):
        return self.__repr__()

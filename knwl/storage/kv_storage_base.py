from abc import ABC, abstractmethod
from typing import Any

from knwl.storage.storage_base import StorageBase


class KeyValueStorageBase(StorageBase, ABC):
    """
    Abstract base class for JSON dictionary storage on disk.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def get_all_ids(self) -> list[str]:
        pass

    @abstractmethod
    async def save(self):
        pass

    @abstractmethod
    async def clear_cache(self):
        pass

    @abstractmethod
    async def get_by_id(self, id):
        pass

    @abstractmethod
    async def get_by_ids(self, ids, fields=None):
        pass

    @abstractmethod
    async def filter_new_ids(self, data: list[str]) -> set[str]:
        pass

    @abstractmethod
    async def upsert(self, obj: Any):
        pass

    @abstractmethod
    async def clear(self):
        pass

    @abstractmethod
    async def count(self):
        pass

    @abstractmethod
    async def delete_by_id(self, id: str):
        pass
    @abstractmethod
    async def exists(self, id: str) -> bool:
        pass
from abc import ABC, abstractmethod

from knwl.storage.storage_base import StorageBase


class KeyValueStorageBase(StorageBase, ABC):
    """
    Abstract base class for JSON dictionary storage on disk.
    """

    def __init__(self, *args, **kwargs):
        pass

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
    async def upsert(self, data: dict[str, object]):
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

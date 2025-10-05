from abc import ABC, abstractmethod

from knwl.storage.storage_base import StorageBase


class VectorStorageBase(StorageBase, ABC):
    """
    Base class for vector storage.
    """

    @abstractmethod
    async def query(self, query: str, top_k: int = 1) -> list[dict]:
        pass

    @abstractmethod
    async def upsert(self, data: dict[str, dict]):
        pass

    @abstractmethod
    async def clear(self):
        pass

    @abstractmethod
    async def count(self):
        pass

    @abstractmethod
    async def get_ids(self):
        pass

    @abstractmethod
    async def save(self):
        pass

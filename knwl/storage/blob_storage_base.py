from abc import ABC, abstractmethod

from knwl.models import KnwlBlob
from knwl.storage.storage_base import StorageBase


class BlobStorageBase(StorageBase, ABC):
    """
    Abstract base class for storing blobs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def upsert(self, blob: KnwlBlob) -> str | None: ...

    @abstractmethod
    async def get_by_id(self, id:str) -> KnwlBlob | None: ...

    @abstractmethod
    async def get_by_id(self, ids, fields=None): ...

    @abstractmethod
    async def delete_by_id(self, id: str) -> bool: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def exists(self, id: str) -> bool: ...

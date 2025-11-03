from abc import ABC, abstractmethod
from typing import Optional

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlDocument import KnwlDocument
from knwl.storage.storage_base import StorageBase


class DocumentBase(FrameworkBase, ABC):
    def __init__(
        self,
        document_storage: Optional[StorageBase] = None,
    ):
        super().__init__()
        self.document_storage: StorageBase = document_storage

    @abstractmethod
    async def upsert(self, obj: str | KnwlDocument) -> str: ...

    @abstractmethod
    async def get_by_id(self, document_id: str) -> KnwlDocument | None: ...

    @abstractmethod
    async def delete_by_id(self, document_id: str) -> None: ...

    @abstractmethod
    async def exists(self, document_id: str) -> bool: ...



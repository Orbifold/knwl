from abc import ABC, abstractmethod
from typing import Optional

from knwl.chunking.chunking_base import ChunkingBase
from knwl.framework_base import FrameworkBase
from knwl.models.KnwlDocument import KnwlDocument
from knwl.storage.storage_adapter import StorageAdapter
from knwl.storage.storage_base import StorageBase
from knwl.storage.vector_storage_base import VectorStorageBase


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


class DocumentStore(DocumentBase):
    async def upsert(self, obj: str | KnwlDocument) -> str:
        if isinstance(obj, str):
            document = KnwlDocument(text=str(obj).strip())
        else:
            document = obj

        await StorageAdapter.upsert(document, self.document_storage)
        return document.id

    async def get_by_id(self, document_id: str) -> KnwlDocument | None:
        return await self.document_storage.get_by_id(document_id)

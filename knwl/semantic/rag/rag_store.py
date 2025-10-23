from knwl import KnwlChunk, KnwlDocument
from knwl.chunking.chunking_base import ChunkingBase
from knwl.di import defaults
from knwl.semantic.rag.rag_base import RagBase
from knwl.storage.storage_base import StorageBase

@defaults("rag_store")
class RagStore(RagBase):
    """
    Default implementation of RagBase.

    Attributes:
        document_storage (StorageBase | None): Storage for documents.
        chunk_storage (StorageBase | None): Storage for chunks.
        chunker (ChunkingBase | None): Chunking strategy.
        auto_chunk (bool): Whether to automatically chunk documents on upsert.
    """

    def __init__(
        self,
        document_storage: StorageBase | None = None,
        chunk_storage: StorageBase | None = None,
        chunker: ChunkingBase | None = None,
        auto_chunk: bool = True,
    ):
        super().__init__()
        self.document_storage: StorageBase = document_storage
        self.chunk_storage: StorageBase = chunk_storage
        self.chunker: ChunkingBase = chunker
        self.auto_chunk: bool = auto_chunk

    async def upsert_document(self, obj: str | KnwlDocument) -> str:
        return await self.document_storage.upsert(obj)

    async def get_document_by_id(self, document_id: str) -> KnwlDocument | None:
        return await self.document_storage.get(document_id)

    async def delete_document_by_id(self, document_id: str) -> None:
        await self.document_storage.delete(document_id)

    async def upsert_chunk(self, obj: str | KnwlChunk) -> str:
        return await self.chunk_storage.upsert(obj)

    async def get_chunk_by_id(self, chunk_id: str) -> KnwlChunk | None:
        return await self.chunk_storage.get(chunk_id)

    async def delete_chunk_by_id(self, chunk_id: str) -> None:
        await self.chunk_storage.delete(chunk_id)

    async def nearest(self, query: str, top_k: int = 5) -> list[KnwlChunk]:
        return await self.chunk_storage.nearest(query, top_k)

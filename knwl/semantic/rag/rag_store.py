from typing import Any
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

    async def upsert(self, obj: Any) -> str:
        if obj is None:
            raise ValueError("RagStore: cannot upsert None object")
        if isinstance(obj, KnwlDocument):
            return await self.upsert_document(obj)
        elif isinstance(obj, KnwlChunk):
            return await self.upsert_chunk(obj)
        elif isinstance(obj, str):
            doc = KnwlDocument(content=obj)
            return await self.upsert_document(doc)
        else:
            raise ValueError(f"RagStore: unsupported upsert object type: {type(obj)}")

    async def upsert_document(self, obj: KnwlDocument) -> str:
        if obj is None:
            raise ValueError("RagStore: cannot upsert None document")
        if not isinstance(obj, KnwlDocument):
            raise ValueError(
                f"RagStore: use the `upsert` method for non-document types, got: {type(obj)}"
            )
        if self.auto_chunk:
            chunks = await self.get_chunks(obj)
            for chunk in chunks:
                await self.upsert_chunk(chunk)

        return await self.document_storage.upsert(obj)

    async def get_chunks(self, doc: KnwlDocument) -> list[KnwlChunk]:
        if self.chunker is None:
            raise ValueError("RagStore: chunker is not configured")
        return await self.chunker.chunk(doc.content, source_key=doc.id)

    async def get_document_by_id(self, document_id: str) -> KnwlDocument | None:
        return await self.document_storage.get(document_id)

    async def delete_document_by_id(self, document_id: str) -> None:
        if document_id is None:
            raise ValueError("RagStore: cannot delete None document_id")
        
        await self.document_storage.delete(document_id)

    async def upsert_chunk(self, obj: str | KnwlChunk) -> str:
        return await self.chunk_storage.upsert(obj)

    async def get_chunk_by_id(self, chunk_id: str) -> KnwlChunk | None:
        return await self.chunk_storage.get(chunk_id)

    async def delete_chunk_by_id(self, chunk_id: str) -> None:
        await self.chunk_storage.delete(chunk_id)

    async def nearest(self, query: str, top_k: int = 5) -> list[KnwlChunk]:
        return await self.chunk_storage.nearest(query, top_k)

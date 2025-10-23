from typing import Optional
from knwl.chunking.chunking_base import ChunkingBase
from knwl.di import defaults
from knwl.models.KnwlChunk import KnwlChunk
from knwl.semantic.rag.chunk_base import ChunkBase
from knwl.storage.storage_adapter import StorageAdapter
from knwl.storage.storage_base import StorageBase
from knwl.storage.vector_storage_base import VectorStorageBase


@defaults("chunk_store")
class ChunkStore(ChunkBase):

    def __init__(
        self,
        chunker: ChunkingBase | None = None,
        chunk_embeddings: VectorStorageBase | None = None,
        chunk_storage: StorageBase | None = None,
    ):
        super().__init__()
        self.chunker: ChunkingBase = chunker
        self.chunk_embeddings: VectorStorageBase = chunk_embeddings
        self.chunk_storage: StorageBase = chunk_storage

    async def upsert(self, obj: str | KnwlChunk) -> str:
        """
        Upserts a text chunk into storage and embeddings.

        Args:
            text (str): The text chunk to be upserted.

        Returns:
            str: The unique identifier of the upserted chunk.
        """
        if isinstance(obj, str):
            chunk = KnwlChunk(content=str(obj).strip())
        else:
            chunk = obj

        await StorageAdapter.upsert(chunk, self.chunk_storage)

        await self.chunk_embeddings.upsert(
            {f"{chunk.id}": chunk.model_dump(mode="json")}
        )
        return chunk.id

    async def get_by_id(self, chunk_id: str) -> KnwlChunk | None:
        """
        Retrieves a text chunk by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk.

        Returns:
            Optional[KnwlChunk]: The retrieved KnwlChunk object if found, otherwise None.
        """
        found = await self.chunk_storage.get_by_id(chunk_id)
        if found is None:
            return None
        elif isinstance(found, KnwlChunk):
            return found
        else:
            return KnwlChunk.model_validate(found)

    async def delete_by_id(self, chunk_id: str) -> None:
        """
        Deletes a text chunk by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk to be deleted.
        """
        await self.chunk_storage.delete_by_id(chunk_id)
        await self.chunk_embeddings.delete_by_id(chunk_id)

    async def exists(self, chunk_id: str) -> bool:
        """
        Checks if a text chunk exists by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk.
        """
        return await self.chunk_storage.exists(chunk_id)

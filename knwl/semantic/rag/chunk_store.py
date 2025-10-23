from knwl.models.KnwlChunk import KnwlChunk
from knwl.semantic.rag.chunk_base import ChunkBase
from knwl.storage.storage_adapter import StorageAdapter


class ChunkStore(ChunkBase):
    async def upsert(self, obj: str | KnwlChunk) -> str:
        """
        Upserts a text chunk into storage and embeddings.

        Args:
            text (str): The text chunk to be upserted.

        Returns:
            str: The unique identifier of the upserted chunk.
        """
        if isinstance(obj, str):
            chunk = KnwlChunk(text=str(obj).strip())
        else:
            chunk = obj

        await StorageAdapter.upsert(chunk, self.chunk_storage)

        await self.chunk_embeddings.upsert(
            {f"{chunk.id}": chunk.model_dump(mode="json")}
        )
        return chunk.id

    async def get_by_id(self, chunk_id: str) -> KnwlChunk|None:
        """
        Retrieves a text chunk by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk.

        Returns:
            Optional[KnwlChunk]: The retrieved KnwlChunk object if found, otherwise None.
        """
        return await self.chunk_storage.get_by_id(chunk_id)
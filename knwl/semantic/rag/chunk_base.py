from abc import ABC, abstractmethod
from typing import Optional

from knwl.chunking.chunking_base import ChunkingBase
from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk
from knwl.storage.storage_base import StorageBase
from knwl.storage.vector_storage_base import VectorStorageBase


class ChunkBase(FrameworkBase, ABC):
    """
    Base class for creating and managing text chunks.
    """

    def __init__(
        self,
        chunker: Optional[ChunkingBase] = None,
        chunk_embeddings: Optional[VectorStorageBase] = None,
        chunk_storage: Optional[StorageBase] = None,
    ):
        super().__init__()
        self.chunker: ChunkingBase = chunker
        self.chunk_embeddings: VectorStorageBase = chunk_embeddings
        self.chunk_storage: StorageBase = chunk_storage

    @abstractmethod
    async def upsert(self, obj: str | KnwlChunk) -> str:
        """
        Upserts a text chunk into storage and embeddings.

        Args:
            text (str): The text chunk to be upserted.

        Returns:
            str: The unique identifier of the upserted chunk.
        """
        ...
    @abstractmethod
    async def get_by_id(self, chunk_id: str) -> KnwlChunk|None:
        """
        Retrieves a text chunk by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk.

        Returns:
            Optional[KnwlChunk]: The retrieved KnwlChunk object if found, otherwise None.
        """
        ...


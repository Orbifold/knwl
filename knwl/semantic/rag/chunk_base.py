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

    @abstractmethod
    async def delete_by_id(self, chunk_id: str) -> None:
        """
        Deletes a text chunk by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk to be deleted.
        """
        ...

    @abstractmethod
    async def exists(self, chunk_id: str) -> bool:
        """
        Checks if a text chunk exists by its unique identifier.

        Args:
            chunk_id (str): The unique identifier of the chunk.
        """
        ...
    @abstractmethod
    async def delete_source(self, source_key: str) -> None:
        """
        Deletes all chunks associated with a given source key.

        Args:
            source_key (str): The source key whose associated chunks are to be deleted.
        """
        ...
    @abstractmethod
    async def get_source_chunks(self, source_key: str) -> list[KnwlChunk]:
        """
        Retrieves all chunks associated with a given source key.

        Args:
            source_key (str): The source key whose associated chunks are to be retrieved.

        Returns:
            list[KnwlChunk]: A list of KnwlChunk objects associated with the source key.
        """
        ...
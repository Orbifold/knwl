from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument


class RagBase(FrameworkBase, ABC):
    """
    Base class to manage documents and chunks.
    The default implementation is `RagStore`, which uses separate storage for documents and chunks. Of course, nothing prevents you to use the same storage for both.
    """

    @abstractmethod
    async def upsert_document(self, obj: str | KnwlDocument) -> str:
        """
        Upserts a document into the document store.

        Args:
            obj (str): The document text to be upserted.

        Returns:
            str: The ID of the upserted document.
        """
        ...

    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> KnwlDocument | None:
        """
        Retrieves a document by its ID.

        Args:
            document_id (str): The ID of the document to retrieve.

        Returns:
            KnwlDocument | None: The retrieved document or None if not found.
        """
        ...
        ...

    @abstractmethod
    async def delete_document_by_id(self, document_id: str) -> None:
        """
        Deletes a document by its ID.

        Args:
            document_id (str): The ID of the document to delete.
        """
        ...

    @abstractmethod
    async def upsert_chunk(self, obj: str | KnwlChunk) -> str:
        """
        Upserts a chunk into the chunk store.

        Args:
            obj (str): The chunk text to be upserted.

        Returns:
            str: The ID of the upserted chunk.
        """
        ...

    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: str) -> KnwlChunk | None:
        """
        Retrieves a chunk by its ID.

        Args:
            chunk_id (str): The ID of the chunk to retrieve.

        Returns:
            KnwlChunk | None: The retrieved chunk or None if not found.
        """
        ...

    @abstractmethod
    async def delete_chunk_by_id(self, chunk_id: str) -> None:
        """
        Deletes a chunk by its ID.

        Args:
            chunk_id (str): The ID of the chunk to delete.
        """
        ...

    @abstractmethod
    async def nearest(self, query: str, top_k: int = 5) -> list[KnwlChunk]:
        """
        Retrieves the nearest chunks based on a query.

        Args:
            query (str): The query string to search for.
            top_k (int): The number of top results to return.

        Returns:
            list[KnwlChunk]: A list of the nearest chunks.
        """
        ...

    @abstractmethod
    async def chunk(self, document: KnwlDocument) -> list[KnwlChunk]:
        ...

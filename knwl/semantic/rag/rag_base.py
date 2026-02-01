from abc import ABC, abstractmethod

from typing import Optional

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

    @abstractmethod
    async def document_count(self) -> int:
        """
        Get the total number of documents in the system.
        """
        ...
    @abstractmethod
    async def get_all_documents(self, amount: int = 10, include_content: bool = False) -> list[KnwlDocument]:
        """
        Retrieve all documents up to the specified amount.

        Args:
            amount (int): The number of documents to retrieve.

        Returns:
            list[KnwlDocument]: A list of retrieved documents.
        """
        ...
    @abstractmethod
    async def chunk_count(self) -> int:
        """
        Get the total number of chunks in the system.
        """
        ...
    @abstractmethod
    async def get_all_chunks(self, amount: int = 10, include_content: bool = False) -> list[KnwlChunk]:
        """
        Retrieve all chunks up to the specified amount.

        Args:
            amount (int): The number of chunks to retrieve.

        Returns:
            list[KnwlChunk]: A list of retrieved chunks.
        """
        ...
    @abstractmethod
    async def get_document_chunks(
        self, document_id: str, include_content: bool = False
    ) -> Optional[list[KnwlChunk]]:
        """
        Retrieve all chunks associated with a specific document.

        Args:
            document_id (str): The unique identifier of the document.
            include_content (bool): Whether to include the content of the chunks.

        Returns:
            Optional[list[KnwlChunk]]: A list of KnwlChunk objects associated with the document, or None if no chunks are found.
        """
        ...
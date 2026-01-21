from abc import ABC, abstractmethod
from typing import Any

from knwl.storage.storage_base import StorageBase


class VectorStorageBase(StorageBase, ABC):
    """Abstract base class for asynchronous vector storage backends.

    Implementations store, index, and query vector embeddings and associated metadata.
    All operations are asynchronous and intended to support large-scale, concurrent
    workloads. Subclasses must implement storage-specific persistence, concurrency
    control, and similarity search semantics.

    Responsibilities:
    - nearest(query: str, top_k: int = 1, where: dict | None = None) -> list[dict]:
        Perform a vector similarity search and return up to top_k results ordered
        by descending similarity. Each result should include identifying information
        (e.g. id), a similarity score, and any associated metadata.
    - upsert(data: dict[str, dict]) -> None:
        Insert or update multiple entries in a single operation. Each value dict
        typically contains an embedding (under 'embedding' or 'embeddings') and
        optional 'metadata'. Implementations may also compute embeddings if not
        provided.
    - clear() -> None:
        Remove all stored vectors and metadata. This is destructive and should be
        made durable according to backend semantics.
    - count() -> int:
        Return the total number of stored vectors.
    - get_ids() -> list[str]:
        Return a list of all stored entry identifiers.
    - save() -> None:
        Persist any in-memory state to durable storage if applicable.
    - get_by_id(id: str) -> dict | None:
        Retrieve the stored entry (embedding and metadata) for a given id, or None
        if not found.
    - delete_by_id(id: str) -> None:
        Remove a specific entry by id.
    - exists(id: str) -> bool:
        Return True if an entry with the given id exists.

    Implementation notes:
    - Implementations should document any backend-specific limitations (consistency,
      transactional guarantees, indexing latency, maximum vector dimensionality).
    - Methods should raise clear exceptions for invalid input or backend failures.
    - Returning structures and metadata keys should be stable and well-documented
      by the concrete storage class to allow consistent consumer behavior.    
    
    """

    @abstractmethod
    async def nearest(self, query: str, top_k: int = 1, where: dict[str, Any] | None = None) -> list[dict]:
        """
        Execute a vector similarity search query against the storage.

        Args:
            query (str): The search query string to find similar vectors for.
            top_k (int, optional): Maximum number of most similar results to return.
                Defaults to 1.

        Returns:
            list[dict]: A list of dictionaries containing the most similar items found,
                ordered by similarity score (highest first). Each dictionary typically
                contains metadata and similarity scores for the matching items.
        """
        ...

    @abstractmethod
    async def upsert(self, data: dict[str, dict]):
        """
        Upsert (insert or update) multiple vector embeddings and their associated metadata.

        This method adds new vectors to the storage or updates existing ones if they already exist.
        The operation is performed asynchronously to handle large datasets efficiently.

        Args:
            data (dict[str, dict]): A dictionary where keys are unique identifiers for the vectors
                                   and values are dictionaries containing vector data and metadata.
                                   Each value dict can optionally contain:
                                   - 'embedding': The embedding vector (list of floats). If not provided,
                                                  the storage may generate it automatically.
                                   - 'embeddings': Alternative key for the embedding vector.
                                   - 'metadata': Additional metadata associated with the vector

        Raises:
            NotImplementedError: This is a base class method that must be implemented by subclasses.
            ValueError: If the data format is invalid or contains malformed vectors.
            StorageError: If there's an error during the upsert operation.

        Returns:
            None: The method performs the upsert operation but doesn't return a value.

        Note:
            This is an abstract method that should be implemented by concrete vector storage classes.
            The specific behavior may vary depending on the underlying storage implementation.
        """
        ...

    @abstractmethod
    async def clear(self): 
        """
        Clear all data from the vector storage.

        This asynchronous coroutine removes every stored vector, document, and associated metadata
        from the underlying storage backend. The operation is destructive and generally irreversible;
        after successful completion the storage should behave as empty.

        Implementations should ensure changes are durably persisted according to the backend's
        semantics and handle any necessary concurrency control (e.g., locks) to avoid races.

        Returns:
            None

        Raises:
            NotImplementedError: If the concrete storage backend does not implement clearing.
            RuntimeError: On I/O, permission, or backend-specific failures that prevent clearing.

        Example:
            await storage.clear()
        """
        ...

    @abstractmethod
    async def count(self): 
        """
        Count the number of vectors stored.

        Returns:
            int: The total number of vectors stored.

        Raises:
            NotImplementedError: If the concrete storage backend does not implement counting.
            RuntimeError: On I/O, permission, or backend-specific failures that prevent counting.

        Example:
            count = await storage.count()
        """
        ...

    @abstractmethod
    async def get_ids(self):  
        """Asynchronously retrieve the identifiers of all entries stored in this vector storage.

        Returns:
            List[str]: A list of unique IDs (typically strings) for the vectors/documents currently
            stored by the backend. Implementations may return any iterable sequence of identifiers,
            but callers should generally expect a list of strings.

        Raises:
            NotImplementedError: If the concrete storage class does not implement this method.
            RuntimeError: Backend-specific errors may be raised if the storage cannot be queried.

        Notes:
            - This is an async method and must be awaited: ids = await storage.get_ids()
            - Implementations should strive to return stable, deduplicated IDs and handle large
            collections efficiently (e.g., pagination) if necessary.
        """
        ...

    @abstractmethod
    async def save(self): 
        """
        Persist any in-memory state or pending changes for this vector storage to durable storage.

        This asynchronous method should flush and synchronize the current vector index, embeddings,
        and any related metadata so that subsequent process restarts or crashes will not lose updates.
        Implementations may write to disk, a database, or a remote service.

        Behavior:
        - Should await completion of all IO and consistency checks before returning.
        - May be a no-op for read-only or ephemeral implementations.
        - Implementations should aim for atomic/transactional semantics where possible.

        Parameters:
        - self: instance of the storage class.

        Returns:
        - None. Implementations may optionally return status information, but callers should not
            rely on a non-None value unless documented by a concrete implementation.

        Raises:
        - IOError/OSError or implementation-specific exceptions on failure.
        - NotImplementedError if the concrete subclass does not support persistence.

        
        """
        ...
    @abstractmethod
    async def get_by_id(self, id: str): ...

    @abstractmethod
    async def delete_by_id(self, id: str): ...

    @abstractmethod
    async def exists(self, id: str) -> bool: ...

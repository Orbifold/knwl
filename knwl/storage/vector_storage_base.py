from abc import ABC, abstractmethod
from typing import Any

from knwl.storage.storage_base import StorageBase


class VectorStorageBase(StorageBase, ABC):
    """
    Base class for vector storage.
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
    async def clear(self): ...

    @abstractmethod
    async def count(self): ...

    @abstractmethod
    async def get_ids(self): ...

    @abstractmethod
    async def save(self): ...

    @abstractmethod
    async def get_by_id(self, id: str): ...

    @abstractmethod
    async def delete_by_id(self, id: str): ...

    @abstractmethod
    async def exists(self, id: str) -> bool: ...

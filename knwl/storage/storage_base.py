from abc import ABC
from typing import Any
from knwl.framework_base import FrameworkBase
from knwl.models import KnwlModel


class StorageBase(FrameworkBase, ABC):
    """
    Base class for diverse storage implementations.
    This class defines the interface and common properties for storage systems.
    """

    pass

    # todo: turn this into abstract methods
    async def get_by_id(self, id: str) -> KnwlModel | None:
        """
        Retrieves an object by its unique identifier.
        """
        return None

    async def delete_by_id(self, id: str) -> None:
        """
        Deletes an object by its unique identifier.
        """
        pass

    async def exists(self, id: str) -> bool:
        """
        Checks if an object exists by its unique identifier.
        """
        return False

    async def upsert(self, obj: KnwlModel) -> str | None:
        """
        Upserts an object into storage and returns its unique identifier.
        """
        return None

    async def nearest(self, query: str, top_k: int = 5, where: dict[str, Any] | None = None) -> list[KnwlModel]:
        """
        Semantic search, retrieves the top_k nearest objects based on a query.
        """
        return []

    async def get_by_metadata(self, **kwargs) -> list[KnwlModel]:
        """
        Retrieves objects based on metadata key-value pairs.
        Future improvements will define a MongoDB-like query language for more complex queries.
        """
        return []

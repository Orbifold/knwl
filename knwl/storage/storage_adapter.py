from typing import Any
from knwl.models import KnwlDocument, KnwlEdge, KnwlGraph, KnwlNode
from knwl.storage.blob_storage_base import BlobStorageBase
from knwl.storage.graph_base import GraphStorageBase
from knwl.storage.kv_storage_base import KeyValueStorageBase
from knwl.storage.storage_base import StorageBase
from knwl.storage.vector_storage_base import VectorStorageBase


class StorageAdapter:
    """
    This sits between Knwl input formats and the diverse storage interfaces.
    It attempts to store whatever you throw at it in the appropriate storage backend.

    """

    @staticmethod
    async def upsert(obj: Any, storage: StorageBase | list[StorageBase]):
        """
        Upserts an object into the given storage backend(s).
        """
        if obj is None:
            raise ValueError("StorageAdapter: cannot upsert None object")
        if not isinstance(storage, list):
            storage = [storage]

        for store in storage:
            if isinstance(store, KeyValueStorageBase):
                pass
            elif isinstance(store, BlobStorageBase):
                pass
            elif isinstance(store, VectorStorageBase):
                pass
            elif isinstance(store, GraphStorageBase):
                pass
            else:
                raise ValueError(
                    f"StorageAdapter: unsupported upsert storage type: {type(store)}"
                )

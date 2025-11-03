from typing import Any
import uuid
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
    async def upsert(obj: Any, storage: StorageBase | list[StorageBase]) -> str:
        """
        Upserts an object into the given storage backend(s).
        """
        if obj is None:
            raise ValueError("StorageAdapter: cannot upsert None object")
        if not isinstance(storage, list):
            storage = [storage]

        for store in storage:
            if store is None:
                continue
            if isinstance(store, KeyValueStorageBase):
                return await store.upsert(StorageAdapter.to_key_value(obj))
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

    @staticmethod
    def to_key_value(obj: Any) -> dict[str, Any]:
        """
        Converts an object to a key-value representation for key-value storage.
        """
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj

        elif hasattr(obj, "id"):
            # single object with id attribute
            return {str(obj.id): obj.model_dump(mode="json")}
        elif hasattr(obj, "model_dump"):
            # single object with model_dump method
            return {
                str(getattr(obj, "id", str(uuid.uuid4()))): obj.model_dump(mode="json")
            }
        elif hasattr(obj, "dict"):
            # single object with dict method
            return {str(getattr(obj, "id", str(uuid.uuid4()))): obj.dict()}

        elif isinstance(obj, (float, int, bool, str, bytes)):
            return {str(uuid.uuid4()): obj}
        else:
            raise ValueError(
                f"StorageAdapter: cannot convert object of type {type(obj)} to dict"
            )

import os
import json
from typing import Any
from uuid import uuid4

from knwl.di import defaults
from knwl.models import KnwlModel
from knwl.semantic.rag.document_base import DocumentBase
from knwl.storage.storage_base import StorageBase
from knwl.storage.storage_adapter import StorageAdapter
from knwl.utils import get_full_path, load_json, write_json


@defaults("document_store")
class JsonDocumentStorage(StorageBase):
    """
    Saves models as individual JSON files in a specified directory.
    Each document is stored in a separate file named <id>.json.
    """

    def __init__(self, root_path: str = None):
        super().__init__()
        self.root_path = root_path
        if self.root_path is None:
            self.root_path = get_full_path("$/user/documents")
        else:
            # create dirs by default
            self.root_path = get_full_path(self.root_path)

    async def get_by_id(self, id: str) -> KnwlModel | None:
        """
        Retrieves an object by its unique identifier. Returns parsed JSON (dict) or None.
        """
        if id is None:
            return None
        file_path = os.path.join(self.root_path, f"{id}.json")
        file_path = get_full_path(file_path)
        data = load_json(file_path)
        return data

    async def delete_by_id(self, id: str) -> None:
        """
        Deletes an object by its unique identifier.
        """
        if id is None:
            return None
        file_path = os.path.join(self.root_path, f"{id}.json")
        file_path = get_full_path(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    async def exists(self, id: str) -> bool:
        """
        Checks if an object exists by its unique identifier.
        """
        if id is None:
            return False
        file_path = os.path.join(self.root_path, f"{id}.json")
        file_path = get_full_path(file_path)
        return os.path.exists(file_path)

    async def upsert(self, obj: KnwlModel) -> str | None:
        """
        Upserts an object into storage and returns its unique identifier.
        """
        if obj is None:
            raise ValueError("JsonDocumentStorage: cannot upsert None object")
        # Convert to key/value using StorageAdapter so we accept Pydantic models, dicts, strings

        j = obj.model_dump()
        if j["id"] is None:
            j["id"] = str(uuid4())

        file_path = os.path.join(self.root_path, f"{j['id']}.json")
        write_json(j, file_path)
        return j["id"]

    async def nearest(
        self, query: str, top_k: int = 5, where: dict[str, Any] | None = None
    ) -> list[KnwlModel]:
        """
        Semantic search is not available for file-based JSON documents.
        """
        raise NotImplementedError(
            "JsonDocumentStorage: semantic search is not available."
        )

    async def get_by_metadata(self, **kwargs) -> list[KnwlModel]:
        """
        Retrieves objects based on metadata key-value pairs.
        Future improvements will define a MongoDB-like query language for more complex queries.
        """
        results: list[KnwlModel] = []
        if not os.path.exists(self.root_path):
            return results
        for fn in os.listdir(self.root_path):
            if not fn.endswith(".json"):
                continue
            file_path = get_full_path(os.path.join(self.root_path, fn))
            data = load_json(file_path)
            if data is None:
                continue
            if all(data.get(k) == v for k, v in kwargs.items()):
                results.append(data)
        return results

    async def count(self) -> int:
        """
        Returns the total number of objects in storage.
        """
        if not os.path.exists(self.root_path):
            return 0
        return len([f for f in os.listdir(self.root_path) if f.endswith(".json")])

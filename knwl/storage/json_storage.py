import os
from dataclasses import asdict
from datetime import datetime
from typing import cast

from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument
from knwl.storage.kv_storage_base import KeyValueStorageBase
from knwl.utils import load_json, logger, write_json, get_full_path


class JsonStorage(KeyValueStorageBase):
    """
    Basic JSON storage implementation with everything in a single file.
    Note that this stores a dictionary of objects, where each object must have a unique 'id' field.
    It doesn't allow arrays of objects at the top level.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the JsonSingleStorage instance.

        Args:
            *args:
                - Use simply "test" as path to create a temporary file in the test directory.
                - Use "memory", "none" or "false" to disable file storage and keep data only in memory.
                - Otherwise, the first argument is treated as the file path to store the JSON data.
            **kwargs:
                enabled: Whether to enable file storage (default: True). If False, data is only kept in memory.
        """
        super().__init__(*args, **kwargs)
        if len(args) > 0:
            if isinstance(args[0], str):
                if args[0] == "test":
                    self.file_path = os.path.join(self.get_test_dir(), f"test_{round(datetime.now().timestamp())}.json", )
                    self.enabled = (False if str(kwargs.get("enabled", "True")) == "False" else True)
                elif args[0] == "memory" or args[0] == "none" or args[0] == "false":
                    self.enabled = False
                    self.file_path = None
                else:
                    self.file_path = args[0]
                    self.enabled = True
        else:
            self.enabled = True if str(kwargs.get("enabled", "True")) == "True" else False
            self.file_path = kwargs.get("path", "data.json")
        if self.enabled:
            if not self.file_path.endswith(".json"):
                raise ValueError(f"File path '{self.file_path}' must end with '.json'.")
            self.file_path = get_full_path(self.file_path)
            self.ensure_path_exists(os.path.dirname(self.file_path))
            self.data = load_json(self.file_path) or {}
            if len(self.data) > 0:
                logger.info(f"Loaded '{self.file_path}' JSON with {len(self.data)} items.")
        else:
            self.data = {}
            self.file_path = None
            self.parent_path = None

    async def get_all_ids(self) -> list[str]:
        """
        Get all keys in the storage.
        Returns: A list of id's (strings).
        """
        return list(self.data.keys())

    async def save(self):
        """
        Save the current data to the JSON file if storage is enabled.
        Returns: None
        """
        if self.enabled:
            write_json(self.data, self.file_path)

    async def clear_cache(self):
        """
        Asynchronously removes the file if it exists.

        This method checks if the file specified by the instance variable `_file_name` exists.
        If the file exists, it removes the file.

        Raises:
            OSError: If an error occurs during file removal.
        """

        if self.enabled and os.path.exists(self.file_path):
            os.remove(self.file_path)

    async def get_by_id(self, id):
        """
        Get a single item by its Id.
        Args:
            id: a string representing the Id of the item to retrieve.
        Returns:

        """
        return self.data.get(id, None)

    async def get_by_ids(self, ids, fields=None):
        """
        Get multiple items by their Ids.
        Args:
            ids: a list of strings representing the Ids of the items to retrieve.
            fields: an optional list of strings representing the fields to include in the result. If None, all fields are included.
        Returns: A list of items corresponding to the provided Ids. If an Id does not exist, None is returned in its place.
        """
        if fields is None:
            return [self.data.get(id, None) for id in ids]
        return [({k: v for k, v in self.data[id].items() if k in fields} if self.data.get(id, None) else None) for id in ids]

    async def filter_new_ids(self, data: list[str]) -> set[str]:
        """
        Filter out IDs that are already present in the storage, returning only unknown Id's.

        Args:
             data: A list of Id's to filter.
        Returns: A set of Id's that are not present in the storage.
        """
        return set([s for s in data if s not in self.data])

    async def upsert(self, data: dict[str, object]):
        left_data = {k: v for k, v in data.items() if k not in self.data}
        for k in left_data:
            if isinstance(left_data[k], KnwlChunk):
                left_data[k] = left_data[k].model_dump(mode="json")

            elif isinstance(left_data[k], KnwlDocument):
                left_data[k] = left_data[k].model_dump(mode="json")
            elif hasattr(left_data[k], "model_dump"):  # Pydantic v2
                left_data[k] = left_data[k].model_dump(mode="json")
            else:
                left_data[k] = cast(dict, left_data[k])
            self.data.update(left_data)
            await self.save()
            return left_data

    async def clear(self):
        """
        Clear all data from the storage and delete the file if it exists.
        """
        self.data = {}
        if self.enabled and os.path.exists(self.file_path):
            os.remove(self.file_path)

    async def count(self):
        """
        Count the number of items in the storage.
        Returns: The number of items in the storage.
        """
        return len(self.data)

    async def delete_by_id(self, id: str):
        """
        Delete a single item by its Id.
        Args:
            id: a string representing the Id of the item to delete.
        Returns: True if the item was deleted, False otherwise.
        """
        if id in self.data:
            del self.data[id]
            await self.save()
            return True
        return False

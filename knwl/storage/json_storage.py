import os
from typing import cast
from knwl.logging import log
from knwl.storage.kv_storage_base import KeyValueStorageBase
from knwl.utils import load_json, write_json, get_full_path
from knwl.di import defaults
from pydantic import BaseModel

@defaults("json")
class JsonStorage(KeyValueStorageBase):
    """
    Basic JSON storage implementation with everything in a single file.
    Note that this stores a dictionary of objects, where each object must have a unique 'id' field.
    It doesn't allow arrays of objects at the top level.
    """

    def __init__(self, path: str = "memory", save_to_disk: bool = True):
        """
        Initialize the JsonSingleStorage instance.
        """
        super().__init__()

        self._path = path
        self._save_to_disk = save_to_disk

        try:
            if (
                self._path == "memory"
                or self._path == "none"
                or self._path == "false"
                or self._path is False
                or (isinstance(self._path, bool) and not self._path)
                or (isinstance(self._save_to_disk, bool) and not self._save_to_disk)
            ):
                self._save_to_disk = False
                self._path = None
            else:
                if not self._path.endswith(".json"):
                    log.warn(
                        f"Json storage path '{self._path}' does not end with .json, appending .json"
                    )
                    self._path += ".json"
                self._path = get_full_path(self._path)
                self._save_to_disk = True

            if self._save_to_disk:
                if os.path.exists(self._path) and not os.path.isdir(self._path):
                    self.data = load_json(self._path) or {}
                    if len(self.data) > 0:
                        log(f"Loaded '{self._path}' JSON with {len(self.data)} items.")
                else:
                    self.data = {}
                    self._path = self._path
            else:
                self.data = {}
                self._path = None
        except Exception as e:
            log(e)

    @property
    def path(self):
        return self._path

    @property
    def save_to_disk(self):
        return self._save_to_disk

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
        if self._save_to_disk:
            write_json(self.data, self._path)

    async def clear_cache(self):
        """
        Asynchronously removes the file if it exists.

        This method checks if the file specified by the instance variable `_file_name` exists.
        If the file exists, it removes the file.

        Raises:
            OSError: If an error occurs during file removal.
        """

        if self._save_to_disk and os.path.exists(self._path):
            os.remove(self._path)

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
        return [
            (
                {k: v for k, v in self.data[id].items() if k in fields}
                if self.data.get(id, None)
                else None
            )
            for id in ids
        ]

    async def filter_new_ids(self, data: list[str]) -> set[str]:
        """
        Filter out IDs that are already present in the storage, returning only unknown Id's.

        Args:
             data: A list of Id's to filter.
        Returns: A set of Id's that are not present in the storage.
        """
        return set([s for s in data if s not in self.data])

    async def upsert(self, data: dict[str, object]):
        """
        Upsert data into the JSON storage.

        This method updates existing data or inserts new data into the storage.

        Args:
            data (dict[str, object]): Dictionary containing key-value pairs to upsert.
                                     Values can be KnwlChunk, KnwlDocument, Pydantic models,
                                     or regular dictionaries.

        Returns:
            dict: Dictionary containing only the newly added data items that were
                  not previously present in storage.
        """
        left_data = {k: v for k, v in data.items() if k not in self.data}
        for k in left_data:
            if isinstance(left_data[k], BaseModel):
                left_data[k] = left_data[k].model_dump(mode="json")

            elif isinstance(left_data[k], BaseModel):
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
        if self._save_to_disk and os.path.exists(self._path):
            os.remove(self._path)

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

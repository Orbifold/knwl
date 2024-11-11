import os
import shutil
from dataclasses import asdict
from typing import cast

from knwl.settings import get_config
from knwl.settings import settings
from knwl.utils import KnwlChunk, KnwlDocument, load_json, logger, write_json, StorageNameSpace


class JsonStorage(StorageNameSpace):
    def __init__(self, namespace: str = "default", cache: bool = False):
        super().__init__(namespace, cache)

        if self.cache:
            self.file_path = os.path.join(get_config("working_dir"), f"json_{self.namespace}", "data.json")
            self.parent_path = os.path.dirname(self.file_path)
            self.data = load_json(self.file_path) or {}
            if len(self.data) > 0:
                logger.info(f"Loaded '{self.namespace}' JSON with {len(self.data)} items.")
        else:
            self.data = {}
            self.file_path = None
            self.parent_path = None

    async def get_all_ids(self) -> list[str]:
        return list(self.data.keys())

    async def save(self):

        if self.cache:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            write_json(self.data, self.file_path)

    async def clear_cache(self):
        """
        Asynchronously removes the file if it exists.

        This method checks if the file specified by the instance variable `_file_name` exists.
        If the file exists, it removes the file.

        Raises:
            OSError: If an error occurs during file removal.
        """

        if self.cache and os.path.exists(self.parent_path):
            shutil.rmtree(self.parent_path)

    async def get_by_id(self, id):
        return self.data.get(id, None)

    async def get_by_ids(self, ids, fields=None):
        if fields is None:
            return [self.data.get(id, None) for id in ids]
        return [({k: v for k, v in self.data[id].items() if k in fields} if self.data.get(id, None) else None) for id in ids]

    async def filter_new_ids(self, data: list[str]) -> set[str]:
        return set([s for s in data if s not in self.data])

    async def upsert(self, data: dict[str, object]):
        left_data = {k: v for k, v in data.items() if k not in self.data}
        for k in left_data:
            if isinstance(left_data[k], KnwlChunk):
                left_data[k] = asdict(left_data[k])


            elif isinstance(left_data[k], KnwlDocument):
                left_data[k] = asdict(left_data[k])
            else:
                left_data[k] = cast(dict, left_data[k])
            self.data.update(left_data)
            return left_data

    async def clear(self):
        self.data = {}

    async def count(self):
        return len(self.data)

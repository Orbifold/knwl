from abc import ABC
from knwl.models import KnwlBlob
from knwl.storage.blob_storage_base import BlobStorageBase
import os
import json
from pathlib import Path
from typing import Any, Optional

from knwl.utils import get_full_path


class FileStorage(BlobStorageBase, ABC):
    """Local file system implementation of blob storage."""

    def __init__(self, base_path: Optional[str] = None):
        super().__init__()

        self.base_path = get_full_path(base_path or "$data/files")

    async def upsert(self, blob: KnwlBlob) -> str | None:
        """Upsert a blob to a file."""
        file_path = os.path.join(self.base_path, blob.id)
        self.validate_blob(blob)
        with open(file_path, "wb") as f:
            f.write(blob.data)
        return blob.id

    async def get_by_id(self, id) -> KnwlBlob | None:
        """Get a blob by id from a file."""
        file_path = os.path.join(self.base_path, id)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            data = f.read()
        return KnwlBlob(id=id, data=data)

    async def delete_by_id(self, id: str) -> bool:
        """Delete a blob by id from a file."""
        file_path = os.path.join(self.base_path, id)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        return True

    async def count(self) -> int:
        """Count the number of blobs in the file storage."""
        return len(os.listdir(self.base_path))

    async def exists(self, id: str) -> bool:
        """Check if a blob exists by id in the file storage."""
        file_path = os.path.join(self.base_path, id)
        return os.path.exists(file_path)

    def validate_blob(self, blob: KnwlBlob) -> None:
        """Validate a blob before storage."""
        if (
            blob is not None
            and blob.id is not None
            and len(blob.id) > 0
            and blob.data is not None
            and len(blob.data) > 0
        ):
            return
        raise ValueError("Invalid blob provided for storage.")

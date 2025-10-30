from abc import ABC
from knwl.di import defaults
from knwl.models import KnwlBlob
from knwl.storage.blob_storage_base import BlobStorageBase
import os
import json
from pathlib import Path
from typing import Any, Optional

from knwl.utils import get_full_path


@defaults("blob", "file_system")
class FileStorage(BlobStorageBase, ABC):
    """
    Local file system implementation of blob storage.

    Stores blobs using a custom binary format that preserves both data and metadata
    in a single file:
    - First 4 bytes: metadata length (as 32-bit unsigned integer, big-endian)
    - Next N bytes: JSON metadata (UTF-8 encoded)
    - Remaining bytes: binary data
    """

    def __init__(self, base_path: Optional[str] = None):
        super().__init__()

        self.base_path = get_full_path(base_path or "$/data/files")

    async def upsert(self, blob: KnwlBlob) -> str | None:
        """
        Upsert a blob to a file with metadata.

        Stores blob in custom format: [metadata_length][metadata_json][binary_data]
        """
        file_path = os.path.join(self.base_path, blob.id)
        self.validate_blob(blob)

        # Prepare metadata (exclude data field)
        metadata = {
            "id": blob.id,
            "name": blob.name,
            "description": blob.description,
            "timestamp": blob.timestamp,
            "type_name": blob.type_name,
            "metadata": json.dumps(blob.metadata or {}),  # Store metadata as JSON string
        }
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        metadata_bytes = metadata_json.encode("utf-8")

        # Write custom format: [4-byte length][metadata][data]
        with open(file_path, "wb") as f:
            # Write metadata length as 4-byte unsigned int (big-endian)
            f.write(len(metadata_bytes).to_bytes(4, byteorder="big"))
            # Write metadata
            f.write(metadata_bytes)
            # Write binary data
            f.write(blob.data)

        return blob.id

    async def get_by_id(self, id) -> KnwlBlob | None:
        """
        Get a blob by id from a file, reconstructing full object with metadata.
        """
        file_path = os.path.join(self.base_path, id)
        if not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as f:
            # Read metadata length (4 bytes)
            metadata_length_bytes = f.read(4)
            if len(metadata_length_bytes) < 4:
                # Fallback for old format (just binary data)
                f.seek(0)
                data = f.read()
                return KnwlBlob(id=id, data=data)

            metadata_length = int.from_bytes(metadata_length_bytes, byteorder="big")

            # Read metadata
            metadata_bytes = f.read(metadata_length)
            metadata = json.loads(metadata_bytes.decode("utf-8"))

            # Read remaining binary data
            data = f.read()

        return KnwlBlob(
            id=metadata.get("id", id),
            name=metadata.get("name", ""),
            description=metadata.get("description", ""),
            timestamp=metadata.get("timestamp"),
            metadata=json.loads(metadata.get("metadata", "{}")) if metadata.get("metadata") else {},
            data=data,
        )

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

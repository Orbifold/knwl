import pytest

from knwl.storage.file_storage import FileStorage
from knwl.models import KnwlBlob
import os
import shutil


@pytest.mark.asyncio
async def test_file_storage_upsert_get_delete():
    # Setup
    storage = FileStorage(base_path="$test/file_storage")
    blob = KnwlBlob(id="test_blob",  data=b"Much ado about nothing.")

    # Test upsert
    blob_id = await storage.upsert(blob)
    assert blob_id == blob.id

    # Test get_by_id
    retrieved_blob = await storage.get_by_id("test_blob")
    assert retrieved_blob is not None
    assert retrieved_blob.id == "test_blob"
    assert retrieved_blob.data == b"Much ado about nothing."

    # Test exists
    exists = await storage.exists("test_blob")
    assert exists is True

    # Test count
    count = await storage.count()
    assert count == 1

    # Test delete_by_id
    deleted = await storage.delete_by_id("test_blob")
    assert deleted is True

    # Verify deletion
    retrieved_blob_after_delete = await storage.get_by_id("test_blob")
    assert retrieved_blob_after_delete is None

    # Cleanup
    shutil.rmtree(storage.base_path, ignore_errors=True)

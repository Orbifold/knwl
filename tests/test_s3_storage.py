import io
import json

import pytest

from knwl.storage.s3_storage import S3Storage
from knwl.models import KnwlBlob
from knwl import services

pytestmark = pytest.mark.basic


class DummyClient:
    def __init__(self):
        self.storage = {}

    def put_object(self, Bucket, Key, Body, Metadata=None):
        # store object as tuple of (body bytes, metadata dict)
        self.storage[Key] = (Body, Metadata or {})
        return {"ETag": '"etag"'}

    def head_object(self, Bucket, Key):
        if Key not in self.storage:
            raise Exception("NotFound")
        body, meta = self.storage[Key]
        return {"Metadata": meta}

    def get_object(self, Bucket, Key):
        if Key not in self.storage:
            raise Exception("NotFound")
        body, meta = self.storage[Key]
        return {"Body": io.BytesIO(body)}

    def delete_object(self, Bucket, Key):
        if Key in self.storage:
            del self.storage[Key]
        return {}

    def list_objects_v2(self, Bucket, **kwargs):
        keys = list(self.storage.keys())
        return {
            "KeyCount": len(keys),
            "Contents": [{"Key": k} for k in keys],
            "IsTruncated": False,
        }


@pytest.mark.asyncio
async def test_s3_storage_upsert_get_delete():
    client = DummyClient()
    storage = S3Storage(bucket_name="test-bucket", client=client)

    blob = KnwlBlob(
        id="test_blob",
        data=b"Much ado about nothing.",
        name="Test Blob",
        description="A blob for testing and experimentation.",
        metadata={"author": "Shakespeare", "year": 1600},
    )

    # upsert
    blob_id = await storage.upsert(blob)
    assert blob_id == blob.id

    # get_by_id
    retrieved = await storage.get_by_id("test_blob")
    assert retrieved is not None
    assert retrieved.id == "test_blob"
    assert retrieved.data == b"Much ado about nothing."
    assert retrieved.name == "Test Blob"
    assert retrieved.description == "A blob for testing and experimentation."
    assert retrieved.metadata == {"author": "Shakespeare", "year": 1600}

    # exists
    exists = await storage.exists("test_blob")
    assert exists is True

    # count
    count = await storage.count()
    assert count == 1

    # delete
    deleted = await storage.delete_by_id("test_blob")
    assert deleted is True

    # after delete
    retrieved_after = await storage.get_by_id("test_blob")
    assert retrieved_after is None

    exists_after = await storage.exists("test_blob")
    assert exists_after is False


@pytest.mark.asyncio
async def test_s3_storage_upsert_metadata_roundtrip():
    client = DummyClient()
    storage = S3Storage(bucket_name="test-bucket", client=client)

    blob = KnwlBlob(
        id="meta_blob",
        data=b"123",
        name="Meta Blob",
        description="Desc",
        metadata={"complex": [1, 2, 3], "nested": {"a": True}},
    )

    await storage.upsert(blob)

    # Directly inspect what was stored in the dummy client
    body, md = client.storage["meta_blob"]
    assert body == b"123"
    assert md.get("name") == "Meta Blob"
    assert md.get("description") == "Desc"
    # knwl_metadata should be JSON
    parsed = json.loads(md.get("knwl_metadata"))
    assert parsed == {"complex": [1, 2, 3], "nested": {"a": True}}


@pytest.mark.asyncio
async def test_seaweed():
    storage: S3Storage = services.get_service("blob", "seaweed")
    assert storage is not None
    assert isinstance(storage, S3Storage)
    assert storage.bucket_name == "knwl-blobs"
    assert storage.region_name == "does-not-matter"

    id = await storage.upsert(
        KnwlBlob(
            id="seaweed_test",
            data=b"Testing Seaweed S3 storage.",
            name="Seaweed Test Blob",
        )
    )
    assert id == "seaweed_test"
    assert await storage.exists(id) is True
    retrieved = await storage.get_by_id(id)
    assert retrieved is not None
    assert retrieved.data == b"Testing Seaweed S3 storage."

    id = await storage.upsert(
        KnwlBlob(
            id="seaweed_test",
            data=b"Another blob for SeaweedFS.",
            name="Blobbing Seaweed",
        )
    )
    assert id == "seaweed_test"
    assert await storage.exists(id) is True
    retrieved = await storage.get_by_id(id)
    assert retrieved is not None
    assert retrieved.data == b"Another blob for SeaweedFS."

    current_count = await storage.count()
    assert current_count >= 1
    await storage.delete_by_id("seaweed_test")
    assert await storage.exists("seaweed_test") is False
    print(f"Upserted blob with id: {id}")

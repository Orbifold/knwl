import pytest

from knwl import services
from knwl.models.KnwlDocument import KnwlDocument
from knwl.storage.json_document_storage import JsonDocumentStorage


@pytest.mark.asyncio
async def test_store_document_crud():
    store = JsonDocumentStorage(root_path="$/tests/documents")
    obj = KnwlDocument(content="This is a test document.", name="Test Doc", id="test1")
    document_id = await store.upsert(obj)
    assert document_id == obj.id
    assert await store.exists("test1")
    retrieved_obj = await store.get_by_id("test1")
    assert retrieved_obj is not None
    assert retrieved_obj["content"] == "This is a test document."
    await store.delete_by_id("test1")
    assert not await store.exists("test1")
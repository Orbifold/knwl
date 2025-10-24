import pytest

from knwl.semantic.rag.document_store import DocumentStore
from tests.library.collect import get_random_library_article


@pytest.mark.asyncio
async def test_document_crud():
    store = DocumentStore()
    article = await get_random_library_article()
    id = await store.upsert(article)
    assert await store.exists(id) is True
    found = await store.get_by_id(id)
    assert found is not None
    assert found.id == id
    await store.delete_by_id(id)
    assert await store.exists(id) is False

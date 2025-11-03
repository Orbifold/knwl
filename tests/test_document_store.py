import pytest

from knwl import services
from knwl.config import reset_config
from knwl.semantic.rag.document_store import DocumentStore
from tests.library.collect import get_random_library_article


@pytest.mark.asyncio
async def test_document_crud():
    reset_config()
    store = services.get_service("document_store")
    assert store is not None, "No document storage service found."

    article = await get_random_library_article()
    if not article:
        pytest.fail("No random article returned.")
    id = await store.upsert(article)
    assert await store.exists(id) is True
    found = await store.get_by_id(id)
    assert found is not None
    assert found.id == id
    await store.delete_by_id(id)
    assert await store.exists(id) is False

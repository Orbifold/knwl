import pytest

from knwl.config import reset_config
from knwl.models.KnwlDocument import KnwlDocument
from knwl.semantic.rag.rag_store import RagStore
from tests.library.collect import get_library_article
pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_rag_store():
    reset_config()
    store = RagStore()
    article = await get_library_article("literature", "Jane Austen")
    doc = KnwlDocument(
        id="jane_austen",
        content=article,
        name="Jane Austen",
        description="An article about Jane Austen.",
    )
    id = await store.upsert(doc)
    assert await store.exists(id) is True

    # let's add another article unrelated to literature
    article = await get_library_article("arts", "Mona Lisa")
    doc = KnwlDocument(
        id="mona_lisa",
        content=article,
        name="Mona Lisa",
        description="An article about the Mona Lisa painting.",
    )
    await store.upsert(doc)

    # search for nearest chunks related to literature
    found = await store.nearest("epistolary novel")
    assert len(found) > 0
    ids = [chunk.origin_id for chunk in found]
    assert "jane_austen" in ids
    print(ids)
    
    # search for nearest chunks related to arts
    found = await store.nearest("Da Vinci")
    assert len(found) > 0
    ids = [chunk.origin_id for chunk in found]
    assert "mona_lisa" in ids
    print(ids)

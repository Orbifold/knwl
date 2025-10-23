import pytest

from knwl.semantic.rag.chunk_store import ChunkStore
from faker import Faker
fake =Faker()

@pytest.mark.asyncio
async def test_crud():
    store = ChunkStore()
    text = fake.text()
    chunk_id = await store.upsert(text)
    assert chunk_id is not None
    chunk = await store.get_by_id(chunk_id)
    assert chunk is not None
    assert chunk.content == text.strip()
    assert await store.exists(chunk_id) is True
    await store.delete_by_id(chunk_id)
    assert await store.exists(chunk_id) is False

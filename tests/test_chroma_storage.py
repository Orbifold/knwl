import pytest

from knwl.settings import settings
from knwl.storage.chroma_storage import ChromaStorage
from knwl.utils import random_name


@pytest.fixture
def dummy_store():
    settings.reset()
    storage = ChromaStorage(namespace="dummy")
    return storage


@pytest.fixture
def dummy_store_with_metadata():
    settings.reset()
    storage = ChromaStorage(namespace="dummy", metadata=["a", "b"])
    return storage


@pytest.mark.asyncio
async def test_chroma_db_upsert(dummy_store):
    key = random_name()
    content = key
    data = {key: {"content": content}}
    await dummy_store.upsert(data)
    result = await dummy_store.query(key, top_k=1)
    # print(await dummy_store.get_ids())
    # print("querying ", key)
    assert len(result) == 1
    assert result[0]["content"] == content


@pytest.mark.asyncio
async def test_upsert_with_metadata(dummy_store_with_metadata):
    key = random_name()
    content = key
    data = {key: {"content": content, "a": 1, "b": 2}}
    await dummy_store_with_metadata.upsert(data)
    result = await dummy_store_with_metadata.query(key, top_k=1)
    assert len(result) == 1
    assert result[0]["content"] == data[key]["content"]


@pytest.mark.asyncio
async def test_query_multiple(dummy_store):
    await dummy_store.clear()
    assert await dummy_store.count() == 0
    data = {"key1": {"content": "data1"}, "key2": {"content": "data2"}}
    await dummy_store.upsert(data)
    result = await dummy_store.query("key", top_k=2)
    assert len(result) == 2
    assert {res["content"] for res in result} == {"data1", "data2"}


@pytest.mark.asyncio
async def test_ids(dummy_store):
    await dummy_store.clear()
    data = {"key1": {"content": "data1"}, "key2": {"content": "data2"}}
    await dummy_store.upsert(data)
    ids = await dummy_store.get_ids()
    assert set(ids) == {"key1", "key2"}


@pytest.mark.asyncio
async def test_auto_embedding():
    # chroma does auto-embedding based on all-MiniLM-L6-v2
    from chromadb import Client
    coll = Client()
    collection = coll.get_or_create_collection(name="test_auto_embedding")
    data = {"key1": "This is a test document."}
    collection.upsert(ids=list(data.keys()), documents=list(data.values()))
    all = collection.get(include=["embeddings"])
    assert len(all["embeddings"][0]) == 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings

import pytest

from knwl.config import get_config
from knwl.services import services
from knwl.storage.chroma_storage import ChromaStorage
from knwl.utils import random_name, get_full_path


@pytest.fixture
def dummy_store():
    storage = ChromaStorage(collection_name="dummy")
    return storage


@pytest.fixture
def dummy_store_with_metadata():
    storage = ChromaStorage(collection_name="dummy", metadata=["a", "b"])
    return storage


@pytest.mark.asyncio
async def test_chroma_db_upsert(dummy_store):
    key = random_name()
    content = key
    data = {key: {"content": content}}
    await dummy_store.upsert(data)
    result = await dummy_store.nearest(key, top_k=1)
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
    result = await dummy_store_with_metadata.nearest(key, top_k=1)
    assert len(result) == 1
    assert result[0]["content"] == data[key]["content"]


@pytest.mark.asyncio
async def test_query_multiple(dummy_store):
    await dummy_store.clear()
    assert await dummy_store.count() == 0
    data = {"key1": {"content": "data1"}, "key2": {"content": "data2"}}
    await dummy_store.upsert(data)
    result = await dummy_store.nearest("key", top_k=2)
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
    assert (
        len(all["embeddings"][0]) == 384
    )  # all-MiniLM-L6-v2 produces 384-dimensional embeddings


@pytest.mark.asyncio
async def test_chroma_via_service():
    chroma = services.create_service("vector")
    assert chroma.path == get_full_path(get_config("vector", "chroma", "path"))
    await chroma.upsert({"a1": {"content": "a1"}})
    names = await chroma.get_collection_names()
    assert chroma.collection_name in names
    config = {
        "vector": {
            "special": {
                "class": "knwl.storage.chroma_storage.ChromaStorage",
                "memory": False,
                "collection_name": "special",
                "path": "$/tests/v2",
            },
        }
    }
    chroma = services.create_service("vector", "special", override=config)
    assert chroma.collection_name == "special"
    await chroma.upsert({"b1": {"content": "b1"}})
    names = await chroma.get_collection_names()
    assert "special" in names
    found = await chroma.get_by_id("b1")
    assert found is not None

@pytest.mark.asyncio
async def test_chroma_memory_service():
    chroma = services.create_service("vector", "memory")
    assert chroma.in_memory is True
    await chroma.upsert({"m1": {"content": "memory data"}})
    found = await chroma.get_by_id("m1")
    assert found is not None
    await chroma.clear()
    found = await chroma.get_by_id("m1")
    assert found is None
    await chroma.upsert({"m2": {"content": "more memory data"}})
    found = await chroma.get_by_id("m2")
    assert found is not None



    
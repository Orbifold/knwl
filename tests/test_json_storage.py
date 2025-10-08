import asyncio
import os
from dataclasses import asdict

import pytest

from knwl.models.KnwlDocument import KnwlDocument
from knwl.storage.json_storage import JsonStorage
from knwl.utils import random_name, load_json


@pytest.fixture
def test_store():
    return JsonStorage("test")


@pytest.mark.asyncio
async def test_all_keys(test_store):
    await test_store.clear()
    await test_store.upsert({"key1": {"value": "data1"}, "key2": {"value": "data2"}})
    keys = await test_store.get_all_ids()
    assert set(keys) == {"key1", "key2"}


@pytest.mark.asyncio
async def test_save_somewhere():
    storage = JsonStorage(f"{JsonStorage.get_test_dir()}/{random_name()}.json")
    data = {"key1": {"value": "data1"}}
    await storage.upsert(data)
    await storage.save()
    file_path = storage.file_path
    assert os.path.exists(file_path)
    # remove the JSON file and the directory again
    os.remove(file_path)


@pytest.mark.asyncio
async def test_get_by_id(test_store):
    await test_store.upsert({"key1": {"value": "data1"}})
    data = await test_store.get_by_id("key1")
    assert data == {"value": "data1"}


@pytest.mark.asyncio
async def test_get_by_ids(test_store):
    await test_store.upsert({"key1": {"value": "data1"}, "key2": {"value": "data2"}})
    data = await test_store.get_by_ids(["key1", "key2"])
    assert data == [{"value": "data1"}, {"value": "data2"}]


@pytest.mark.asyncio
async def test_filter_keys(test_store):
    from faker import Faker
    fake = Faker()
    k1 = fake.word()
    k2 = fake.word()
    await test_store.upsert({k1: {"value": "data1"}})
    filtered_keys = await test_store.filter_new_ids([k1, k2])
    assert filtered_keys == {k2}


@pytest.mark.asyncio
async def test_upsert(test_store):
    data = {"key1": {"value": "data1"}}
    await test_store.upsert(data)
    stored_data = await test_store.get_by_id("key1")
    assert stored_data == data["key1"]


@pytest.mark.asyncio
async def test_drop(test_store):
    await test_store.upsert({"key1": {"value": "data1"}})
    await test_store.clear()
    keys = await test_store.get_all_ids()
    assert keys == []


@pytest.mark.asyncio
async def test_save_source(test_store):
    id = random_name()
    source = KnwlDocument(id)
    await test_store.upsert({id: source})
    print()
    found = await test_store.get_by_id(id)
    print(found)
    await test_store.save()
    assert found == asdict(source)


@pytest.mark.asyncio
async def test_save():
    store = JsonStorage("test")
    await store.clear_cache()
    await store.clear()

    data = {"key1": {"value": "data1"}}
    await store.upsert(data)
    await store.save()
    file_path = store.file_path
    await asyncio.sleep(1)  # give os a moment to write the file
    assert os.path.exists(file_path)
    data = load_json(file_path)
    assert data == {"key1": {"value": "data1"}}
    await store.clear_cache()
    assert not os.path.exists(file_path)


@pytest.mark.asyncio
async def test_memory_only():
    store = JsonStorage("test", enabled=False)
    await store.clear_cache()
    await store.clear()

    data = {"key1": {"value": "data1"}}
    await store.upsert(data)
    await store.save()
    assert store.file_path is None
    found = await store.get_by_id("key1")
    assert found == {"value": "data1"}
    await store.clear_cache()

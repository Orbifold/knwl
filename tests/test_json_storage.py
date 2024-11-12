import asyncio
from dataclasses import asdict
import shutil

import pytest
import os

from knwl.jsonStorage import JsonStorage
from knwl.settings import settings

from knwl.utils import random_name, load_json, write_json, KnwlDocument


@pytest.fixture
def dummy_store():
    namespace = "dummy"
    settings.reset()
    storage = JsonStorage(namespace=namespace)
    return storage


@pytest.mark.asyncio
async def test_all_keys(dummy_store):
    await dummy_store.clear()
    await dummy_store.upsert({"key1": {"value": "data1"}, "key2": {"value": "data2"}})
    keys = await dummy_store.get_all_ids()
    assert set(keys) == {"key1", "key2"}


@pytest.mark.asyncio
async def test_save_somewhere():
    namespace = random_name()
    settings.working_dir = f"./{random_name()}"
    storage = JsonStorage(namespace=namespace, cache=True)
    data = {"key1": {"value": "data1"}}
    await storage.upsert(data)
    await storage.save()
    file_path = storage.file_path
    assert os.path.exists(file_path)
    # remove the JSON file and the directory again
    # os.remove(file_path)
    shutil.rmtree(settings.working_dir)  # os.rmdir(settings.working_dir)


@pytest.mark.asyncio
async def test_get_by_id(dummy_store):
    await dummy_store.upsert({"key1": {"value": "data1"}})
    data = await dummy_store.get_by_id("key1")
    assert data == {"value": "data1"}


@pytest.mark.asyncio
async def test_get_by_ids(dummy_store):
    await dummy_store.upsert({"key1": {"value": "data1"}, "key2": {"value": "data2"}})
    data = await dummy_store.get_by_ids(["key1", "key2"])
    assert data == [{"value": "data1"}, {"value": "data2"}]


@pytest.mark.asyncio
async def test_filter_keys(dummy_store):
    await dummy_store.upsert({"key1": {"value": "data1"}})
    filtered_keys = await dummy_store.filter_new_ids(["key1", "key2"])
    assert filtered_keys == {"key2"}


@pytest.mark.asyncio
async def test_upsert(dummy_store):
    data = {"key1": {"value": "data1"}}
    await dummy_store.upsert(data)
    stored_data = await dummy_store.get_by_id("key1")
    assert stored_data == data["key1"]


@pytest.mark.asyncio
async def test_drop(dummy_store):
    await dummy_store.upsert({"key1": {"value": "data1"}})
    await dummy_store.clear()
    keys = await dummy_store.get_all_ids()
    assert keys == []


@pytest.mark.asyncio
async def test_save_source(dummy_store):
    id = random_name()
    source = KnwlDocument(id)
    await dummy_store.upsert({id: source})
    print()
    found = await dummy_store.get_by_id(id)
    print(found)
    await dummy_store.save()
    assert found == asdict(source)


@pytest.mark.asyncio
async def test_save():
    store = JsonStorage("dummy", True)
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

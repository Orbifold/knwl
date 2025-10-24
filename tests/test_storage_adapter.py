import pytest
from knwl.storage.storage_adapter import StorageAdapter
from tests.fixtures import random_node
pytestmark = pytest.mark.basic
    

def test_key_value(random_node):
    u = {"a": 1, "b": 2}
    assert StorageAdapter.to_key_value(u) == u
    u = 3.4
    d = StorageAdapter.to_key_value(u)
    assert isinstance(d, dict) and list(d.values()) == [u]
    u = random_node
    d = StorageAdapter.to_key_value(u)

    assert isinstance(d, dict)
    assert list(d.keys())[0] == str(u.id)
    assert list(d.values())[0]["name"] == u.name

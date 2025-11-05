import os
import random

import pytest

from knwl.models.KnwlNode import KnwlNode
from knwl.storage.networkx_storage import NetworkXGraphStorage

pytestmark = pytest.mark.basic


@pytest.fixture
def test_storage():
    return NetworkXGraphStorage()


@pytest.mark.asyncio
async def test_upsert_node(test_storage):
    await test_storage.upsert_node("node1", {"name": "xws"})
    node = await test_storage.get_node_by_id("node1")
    assert node["name"] == "xws"
    # you can add anything you like since it's a dict
    await test_storage.upsert_node({"id": "node1", "name": "xws2", "x": 44})
    node = await test_storage.get_node_by_id("node1")
    assert node["name"] == "xws2"
    assert node["x"] == 44
    await test_storage.upsert_node("node1", {"x": 55})
    node = await test_storage.get_node_by_id("node1")
    assert node["name"] == "xws2"
    assert node["x"] == 55

    # one or the other
    with pytest.raises(ValueError):
        await test_storage.upsert_node({"id": "node1", "x": {"a": 5}}, {"x": 5})

    with pytest.raises(ValueError):
        await test_storage.upsert_node(5)
    with pytest.raises(ValueError):
        await test_storage.upsert_node(None)

    with pytest.raises(ValueError):
        await test_storage.upsert_node({"x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node({})
    with pytest.raises(ValueError):
        await test_storage.upsert_node([], {})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", [])
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", 5)

    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": "node2", "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": 5, "x": 5})
    with pytest.warns(UserWarning):
        await test_storage.upsert_node("node1", {"id": None, "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": {}, "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": [], "x": 5})


@pytest.mark.asyncio
async def test_upsert_edge(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge(
        "node1", "node2", {"id": "e1", "weight": 2.35, "type": "A"}
    )
    await test_storage.upsert_edge(
        "node1", "node2", {"id": "e2", "weight": -0.45, "type": "B"}
    )
    edges = await test_storage.get_edges("node1", "node2")
    assert len(edges) == 2
    assert edges[0]["weight"] == 2.35
    edges = await test_storage.get_edges("node1", "node2", "B")
    assert len(edges) == 1
    assert edges[0]["weight"] == -0.45
    assert await test_storage.node_count() == 2
    assert await test_storage.edge_count() == 2
    await test_storage.upsert_edge(
        "node1", "node2", {"id": "e1", "weight": 17, "type": "A"}
    )
    assert await test_storage.edge_count() == 2
    edges = await test_storage.get_edges("node1", "node2")
    assert len(edges) == 2
    weights = set(e["weight"] for e in edges)
    assert weights == {17, -0.45}
    types = set(e["type"] for e in edges)
    assert types == {"A", "B"}
    ids = set(e["id"] for e in edges)
    assert ids == {"e1", "e2"}


@pytest.mark.asyncio
async def test_has_node(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    has_node = await test_storage.node_exists("node1")
    assert has_node is True


@pytest.mark.asyncio
async def test_has_edge(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    e = await test_storage.upsert_edge("node1", "node2", {"weight": "1"})
    print("")
    print(e)
    has_edge = await test_storage.edge_exists("node1", "node2")
    assert has_edge is True


@pytest.mark.asyncio
async def test_node_degree(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"weight": "1"})
    degree = await test_storage.node_degree("node1")
    assert degree == 1


@pytest.mark.asyncio
async def test_edge_degree(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"weight": "1"})
    degree = await test_storage.edge_degree("node1", "node2")
    assert degree == 2


@pytest.mark.asyncio
async def test_get_nodes_edges(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_node("node3", {"description": "value3"})
    e1 = await test_storage.upsert_edge("node1", "node2", {"weight": 1.3})
    e2 = await test_storage.upsert_edge("node1", "node3", {"weight": 4.5})
    edges = await test_storage.get_node_edges("node1")
    assert [e["weight"] for e in edges] == [1.3, 4.5]


@pytest.mark.asyncio
async def test_save(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.save()
    assert test_storage.path is None


@pytest.mark.asyncio
async def test_remove_node(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    weight = random.normalvariate()
    await test_storage.upsert_edge("node1", "node2", {"weight": f"{weight}"})
    weights = await test_storage.get_edge_weights("node1", "node2")
    assert weights == {"Unknown": weight}
    assert await test_storage.get_edge_weights("node21", "node25") == {}

    await test_storage.remove_node("node1")
    has_node = await test_storage.node_exists("node1")
    assert has_node is False
    has_edge = await test_storage.edge_exists("node1", "node2")
    assert has_edge is False


@pytest.mark.asyncio
async def test_edge_exists(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"weight": 1.3})
    assert await test_storage.edge_exists("node1", "node2")
    assert await test_storage.edge_exists("node2", "node1") == False  # directed graph
    assert await test_storage.edge_exists("(node1, node2)")


@pytest.mark.asyncio
async def test_edge_exists_with_tuple(test_storage):
    test_storage.graph.add_edge("node1", "node2")
    assert await test_storage.edge_exists(("node1", "node2")) is True


@pytest.mark.asyncio
async def test_edge_exists_with_string_tuple(test_storage):
    test_storage.graph.add_edge("node1", "node2")
    assert await test_storage.edge_exists("(node1, node2)") is True


@pytest.mark.asyncio
async def test_edge_exists_with_dict(test_storage):
    test_storage.graph.add_edge("node1", "node2")
    assert await test_storage.edge_exists({"id": "node1"}, {"id": "node2"}) is True


@pytest.mark.asyncio
async def test_edge_exists_with_knwl_node(test_storage):
    n1 = KnwlNode(name="node1", type="W")
    n2 = KnwlNode(name="node2", type="K")
    # nodes must exist before adding an edge
    with pytest.raises(ValueError):
        await test_storage.upsert_edge(n1, n2)
    await test_storage.upsert_node(n1)
    await test_storage.upsert_node(n2)
    # will now work
    await test_storage.upsert_edge(n1, n2)

    assert await test_storage.edge_exists(n1.id, n2.id) is True


@pytest.mark.asyncio
async def test_get_node_by_name(test_storage):
    # Add nodes to the graph
    node1 = KnwlNode(name="Node1", type="A")
    node2 = KnwlNode(name="Node2", type="K")
    node3 = KnwlNode(name="Node1", type="B")  # Same name as node1

    await test_storage.upsert_node(node1)
    await test_storage.upsert_node(node2)
    await test_storage.upsert_node(node3)

    # Test get_node_by_name for "Node1"
    result = await test_storage.get_nodes_by_name("Node1")
    assert len(result) == 2
    assert set([n["name"] for n in result]) == {"Node1"}
    assert set([n["type"] for n in result]) == {"A", "B"}

    # Test get_node_by_name for "Node2"
    result = await test_storage.get_nodes_by_name("Node2")
    assert len(result) == 1
    assert result[0]["id"] == node2.id

    # Test get_node_by_name for a non-existent node name
    result = await test_storage.get_nodes_by_name("NonExistentNode")
    assert result == []


@pytest.mark.asyncio
async def test_get_edge_weight_default_weight(test_storage):
    test_storage = NetworkXGraphStorage(memory=True)
    source_node_id = "node1"
    target_node_id = "node2"

    # Add nodes and edge without weight to the graph
    await test_storage.upsert_node(source_node_id, {"name": "Node 1"})
    await test_storage.upsert_node(target_node_id, {"name": "Node 2"})
    await test_storage.upsert_edge(source_node_id, target_node_id, {})

    # Test get_edge_weight for edge with default weight
    result = await test_storage.get_edge_weights(source_node_id, target_node_id)
    assert result["Unknown"] == 1.0


@pytest.mark.asyncio
async def test_remove_edge_with_tuple(test_storage):
    n1 = await test_storage.upsert_node(KnwlNode(name="Node 1", type="A"))
    n2 = await test_storage.upsert_node(KnwlNode(name="Node 2", type="K"))
    await test_storage.upsert_edge(n1, n2)

    assert await test_storage.edge_exists(n1, n2)

    await test_storage.remove_edge(n1, n2)

    assert not await test_storage.edge_exists(n1, n2)


@pytest.mark.asyncio
async def test_get_edges():
    g = NetworkXGraphStorage(memory=True)
    n1 = await g.upsert_node(KnwlNode(name="Node 1", type="A"))
    n2 = await g.upsert_node(KnwlNode(name="Node 2", type="K"))
    e1 = await g.upsert_edge(n1, n2, {"type": "relates_to"})
    e2 = await g.upsert_edge(n1, n2, {"type": "connected_to"})

    edges = await g.get_edges_between_nodes(n1["id"], n2["id"])
    assert len(edges) == 2
    assert edges[0]["id"] == e1["id"]
    assert edges[0]["type"] == "relates_to"
    assert edges[1]["id"] == e2["id"]
    assert edges[1]["type"] == "connected_to"

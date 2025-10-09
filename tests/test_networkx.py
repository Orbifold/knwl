import os
import random

import pytest

from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.storage.networkx_storage import NetworkXGraphStorage


@pytest.fixture
def test_storage():
    return NetworkXGraphStorage("memory")


@pytest.mark.asyncio
async def test_upsert_node(test_storage):
    await test_storage.upsert_node("node1", {"name": "xws"})
    node = await test_storage.get_node_by_id("node1")
    assert node["name"] == "xws"
    assert os.path.exists(test_storage.path)
    # you can add anything you like since it's a dict
    await test_storage.upsert_node({"id": "node1", "name": "xws2", "x": 44})
    node = await test_storage.get_node_by_id("node1")
    assert node["name"] == "xws2"
    assert node["x"] == 44
    await test_storage.upsert_node("node1", {"x": 55})
    node = await test_storage.get_node_by_id("node1")
    assert node["name"] == "xws2"
    assert node["x"] == 55
    # complex nested dicts are not allowed by nx
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"x": {"a": 5}})

    # one or the other
    with pytest.raises(ValueError):
        await test_storage.upsert_node({"id": "node1", "x": {"a": 5}}, {"x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("a")
    with pytest.raises(ValueError):
        await test_storage.upsert_node(5)
    with pytest.raises(ValueError):
        await test_storage.upsert_node(None)
    with pytest.raises(ValueError):
        await test_storage.upsert_node({"id": "node1", "x": {"a": 5}})
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
        await test_storage.upsert_node("node1", None)
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": "node2", "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": 5, "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": None, "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": {}, "x": 5})
    with pytest.raises(ValueError):
        await test_storage.upsert_node("node1", {"id": [], "x": 5})


@pytest.mark.asyncio
async def test_upsert_edge(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"id": "e1", "weight": 2.35, "type": "A"})
    await test_storage.upsert_edge("node1", "node2", {"id": "e2", "weight": -0.45, "type": "B"})
    edges = await test_storage.get_edges("node1", "node2")
    assert len(edges) == 2
    assert edges[0]["weight"] == 2.35
    edges = await test_storage.get_edges("node1", "node2", "B")
    assert len(edges) == 1
    assert edges[0]["weight"] == -0.45
    assert await test_storage.node_count() == 2
    assert await test_storage.edge_count() == 2
    await test_storage.upsert_edge("node1", "node2", {"id": "e1", "weight": 17, "type": "A"})
    assert await test_storage.edge_count() == 2
    edges = await test_storage.get_edges("node1", "node2")
    assert len(edges) == 2
    weights = set(e["weight"] for e in edges)
    assert weights == {17, -0.45}

@pytest.mark.asyncio
async def test_has_node(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    has_node = await test_storage.node_exists("node1")
    assert has_node is True


@pytest.mark.asyncio
async def test_has_edge(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"weight": "1"})
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
async def test_get_node_edges(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"weight": 1.3})
    await test_storage.upsert_edge("node1", "node3", {"weight": 4.5})
    edges = await test_storage.get_node_edges("node1")
    assert [e.weight for e in edges] == [1.3, 4.5]


@pytest.mark.asyncio
async def test_save():
    store = NetworkXGraphStorage(memory=True)
    await store.upsert_node("node1", {"description": "value1"})
    await store.save()
    assert store.path is None


@pytest.mark.asyncio
async def test_remove_node(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    weight = random.normalvariate()
    await test_storage.upsert_edge("node1", "node2", {"weight": f"{weight}"})
    weight = await test_storage.get_edge_weight("node1", "node2")
    assert weight == f"{weight}"
    with pytest.raises(ValueError):
        weight = await test_storage.get_edge_weight("node21", "node25")

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
    assert await test_storage.edge_exists("node2", "node1")  # undirected graph
    assert await test_storage.edge_exists("(node1, node2)")


def test_from_knwl_edge_with_valid_edge():
    edge = KnwlEdge(source_id="node1", target_id="node2", weight=1.0)
    expected = edge.model_dump(mode="json")
    result = NetworkXGraphStorage.from_knwl_edge(edge)
    assert result == expected


def test_from_knwl_edge_with_none():
    result = NetworkXGraphStorage.from_knwl_edge(None)
    assert result is None


@pytest.mark.asyncio
async def test_edge_exists_with_valid_edge():
    graph_storage = NetworkXGraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists("node1", "node2") is True


@pytest.mark.asyncio
async def test_edge_exists_with_invalid_edge():
    graph_storage = NetworkXGraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists("node1", "node3") is False


@pytest.mark.asyncio
async def test_edge_exists_with_edge_object():
    graph_storage = NetworkXGraphStorage()
    edge = KnwlEdge(source_id="node1", target_id="node2")
    graph_storage.graph.add_edge(edge.source_id, edge.target_id)
    assert await graph_storage.edge_exists(edge)


@pytest.mark.asyncio
async def test_edge_exists_with_tuple():
    graph_storage = NetworkXGraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists(("node1", "node2")) is True


@pytest.mark.asyncio
async def test_edge_exists_with_invalid_format():
    graph_storage = NetworkXGraphStorage()
    with pytest.raises(ValueError):
        await graph_storage.edge_exists("(node1-node2)")


@pytest.mark.asyncio
async def test_edge_exists_with_dict():
    graph_storage = NetworkXGraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists({"source_id": "node1"}, {"target_id": "node2"}) is True


@pytest.mark.asyncio
async def test_edge_exists_with_knwl_node():
    graph_storage = NetworkXGraphStorage()
    node1 = KnwlNode(id="node1", name="node1")
    node2 = KnwlNode(id="node2", name="node2")
    graph_storage.graph.add_edge(node1.id, node2.id)
    assert await graph_storage.edge_exists(node1, node2)


@pytest.mark.asyncio
async def test_get_node_by_name():
    # Create a GraphStorage instance
    graph_storage = NetworkXGraphStorage(path=None)

    # Add nodes to the graph
    node1 = KnwlNode(name="Node1", type="A")
    node2 = KnwlNode(name="Node2", type="K")
    node3 = KnwlNode(name="Node1", type="B")  # Same name as node1

    await graph_storage.upsert_node(node1.id, node1)
    await graph_storage.upsert_node(node2.id, node2)
    await graph_storage.upsert_node(node3.id, node3)

    # Test get_node_by_name for "Node1"
    result = await graph_storage.get_node_by_name("Node1")
    assert len(result) == 2
    assert any(node.id == node1.id for node in result)
    assert any(node.id == node3.id for node in result)

    # Test get_node_by_name for "Node2"
    result = await graph_storage.get_node_by_name("Node2")
    assert len(result) == 1
    assert result[0].id == node2.id

    # Test get_node_by_name for a non-existent node name
    result = await graph_storage.get_node_by_name("NonExistentNode")
    assert result == []


@pytest.mark.asyncio
async def test_get_edges_empty_graph():
    graph_storage = NetworkXGraphStorage(memory=True)
    edges = await graph_storage.get_edges()
    assert edges == []


@pytest.mark.asyncio
async def test_get_edges_with_edges():
    graph_storage = NetworkXGraphStorage(path=None)
    node1 = KnwlNode(id="1", name="Node 1")
    node2 = KnwlNode(id="2", name="Node 2")
    edge = KnwlEdge(source_id="1", target_id="2", weight=1.0)

    await graph_storage.upsert_node(node1.id, node1)
    await graph_storage.upsert_node(node2.id, node2)
    await graph_storage.upsert_edge(edge.source_id, edge.target_id, edge)

    edges = await graph_storage.get_edges()
    assert len(edges) == 1
    assert edges[0].source_id == "1"
    assert edges[0].target_id == "2"
    assert edges[0].weight == 1.0


@pytest.mark.asyncio
async def test_get_edge_weight_existing_edge():
    graph_storage = NetworkXGraphStorage()
    source_node_id = "node1"
    target_node_id = "node2"
    weight = 2.5

    # Add nodes and edge to the graph
    await graph_storage.upsert_node(source_node_id, {"name": "Node 1"})
    await graph_storage.upsert_node(target_node_id, {"name": "Node 2"})
    await graph_storage.upsert_edge(source_node_id, target_node_id, {"weight": weight})

    # Test get_edge_weight
    result = await graph_storage.get_edge_weight(source_node_id, target_node_id)
    assert result == weight


@pytest.mark.asyncio
async def test_get_edge_weight_non_existing_edge():
    graph_storage = NetworkXGraphStorage(path=None)
    source_node_id = "node1"
    target_node_id = "node2"

    # Add nodes without adding an edge
    await graph_storage.upsert_node(source_node_id, {"name": "Node 1"})
    await graph_storage.upsert_node(target_node_id, {"name": "Node 2"})

    # Test get_edge_weight for non-existing edge
    with pytest.raises(ValueError, match=f"Edge {source_node_id} -> {target_node_id} does not exist"):
        await graph_storage.get_edge_weight(source_node_id, target_node_id)


@pytest.mark.asyncio
async def test_get_edge_weight_default_weight():
    graph_storage = NetworkXGraphStorage(memory=True)
    source_node_id = "node1"
    target_node_id = "node2"

    # Add nodes and edge without weight to the graph
    await graph_storage.upsert_node(source_node_id, {"name": "Node 1"})
    await graph_storage.upsert_node(target_node_id, {"name": "Node 2"})
    await graph_storage.upsert_edge(source_node_id, target_node_id, {})

    # Test get_edge_weight for edge with default weight
    result = await graph_storage.get_edge_weight(source_node_id, target_node_id)
    assert result == 1.0


@pytest.mark.asyncio
async def test_get_edge_weight_knwl_edge():
    graph_storage = NetworkXGraphStorage()
    source_node_id = "node1"
    target_node_id = "node2"
    weight = 3.5
    edge = KnwlEdge(source_id=source_node_id, target_id=target_node_id, weight=weight)

    # Add nodes and edge to the graph
    await graph_storage.upsert_node(source_node_id, {"name": "Node 1"})
    await graph_storage.upsert_node(target_node_id, {"name": "Node 2"})
    await graph_storage.upsert_edge(source_node_id, target_node_id, edge.model_dump(mode="json"))

    # Test get_edge_weight using KnwlEdge instance
    result = await graph_storage.get_edge_weight(edge)
    assert result == weight


@pytest.mark.asyncio
async def test_remove_edge_with_edge_object():
    graph_storage = NetworkXGraphStorage()
    edge = KnwlEdge(source_id="node1", target_id="node2", weight=1.0)
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge(edge)

    assert await graph_storage.edge_exists(edge)

    await graph_storage.remove_edge(edge)

    assert not await graph_storage.edge_exists(edge)


@pytest.mark.asyncio
async def test_remove_edge_with_tuple():
    graph_storage = NetworkXGraphStorage()
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge("node1", "node2", KnwlEdge(source_id="node1", target_id="node2", weight=1.0))

    assert await graph_storage.edge_exists("node1", "node2")

    await graph_storage.remove_edge(("node1", "node2"))

    assert not await graph_storage.edge_exists("node1", "node2")


@pytest.mark.asyncio
async def test_remove_edge_with_node_objects():
    graph_storage = NetworkXGraphStorage()
    node1 = KnwlNode(id="node1", name="Node 1")
    node2 = KnwlNode(id="node2", name="Node 2")
    await graph_storage.upsert_node(node1.id, node1)
    await graph_storage.upsert_node(node2.id, node2)
    await graph_storage.upsert_edge(node1.id, node2.id, KnwlEdge(source_id=node1.id, target_id=node2.id, weight=1.0))

    assert await graph_storage.edge_exists(node1.id, node2.id)

    await graph_storage.remove_edge(node1, node2)

    assert not await graph_storage.edge_exists(node1.id, node2.id)


@pytest.mark.asyncio
async def test_remove_edge_with_node_ids():
    graph_storage = NetworkXGraphStorage()
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge("node1", "node2", KnwlEdge(source_id="node1", target_id="node2", weight=1.0))

    assert await graph_storage.edge_exists("node1", "node2")

    await graph_storage.remove_edge("node1", "node2")

    assert not await graph_storage.edge_exists("node1", "node2")


@pytest.mark.asyncio
async def test_remove_edge_with_invalid_data():
    graph_storage = NetworkXGraphStorage()
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge("node1", "node2", KnwlEdge(source_id="node1", target_id="node2", weight=1.0))

    with pytest.raises(ValueError):
        await graph_storage.remove_edge("node1")


@pytest.mark.asyncio
async def test_get_nodes_empty_graph():
    storage = NetworkXGraphStorage(path=None)
    assert await storage.node_count() == 0


@pytest.mark.asyncio
async def test_get_nodes_with_nodes():
    storage = NetworkXGraphStorage(memory=True)
    node1 = KnwlNode(name="Node1")
    node2 = KnwlNode(name="Node2")
    await storage.upsert_node(node1.id, node1)
    await storage.upsert_node(node2.id, node2)

    assert await storage.node_count() == 2

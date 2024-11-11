import os
import random
from dataclasses import asdict

import pytest

from knwl.graphStorage import GraphStorage

from knwl.settings import settings
from knwl.utils import random_name, KnwlEdge, KnwlNode


@pytest.fixture
def test_storage():
    return GraphStorage(namespace="test")


@pytest.mark.asyncio
async def test_upsert_node(test_storage):
    await test_storage.upsert_node("node1", {"name": "xws"})
    node = await test_storage.get_node_by_id("node1")
    assert node.name == "xws"


@pytest.mark.asyncio
async def test_upsert_edge(test_storage):
    await test_storage.upsert_node("node1", {"description": "value1"})
    await test_storage.upsert_node("node2", {"description": "value2"})
    await test_storage.upsert_edge("node1", "node2", {"weight": 2.35})
    edge_data = await test_storage.get_edge("node1", "node2")
    assert edge_data.weight == 2.35


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

    store = GraphStorage(namespace=random_name(), cache=True)
    await store.upsert_node("node1", {"description": "value1"})
    await store.save()
    file_path = store.file_path
    assert os.path.exists(file_path)
    await store.unsave()
    assert not os.path.exists(file_path)
    settings.reset()  # reset for the remaining tests


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
    edge = KnwlEdge(sourceId="node1", targetId="node2", weight=1.0)
    expected = asdict(edge)
    result = GraphStorage.from_knwl_edge(edge)
    assert result == expected


def test_from_knwl_edge_with_none():
    result = GraphStorage.from_knwl_edge(None)
    assert result is None


@pytest.mark.asyncio
async def test_edge_exists_with_valid_edge():
    graph_storage = GraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists("node1", "node2") is True


@pytest.mark.asyncio
async def test_edge_exists_with_invalid_edge():
    graph_storage = GraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists("node1", "node3") is False


@pytest.mark.asyncio
async def test_edge_exists_with_edge_object():
    graph_storage = GraphStorage()
    edge = KnwlEdge(sourceId="node1", targetId="node2")
    graph_storage.graph.add_edge(edge.sourceId, edge.targetId)
    assert await graph_storage.edge_exists(edge)


@pytest.mark.asyncio
async def test_edge_exists_with_tuple():
    graph_storage = GraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists(("node1", "node2")) is True


@pytest.mark.asyncio
async def test_edge_exists_with_invalid_format():
    graph_storage = GraphStorage()
    with pytest.raises(ValueError):
        await graph_storage.edge_exists("(node1-node2)")


@pytest.mark.asyncio
async def test_edge_exists_with_dict():
    graph_storage = GraphStorage()
    graph_storage.graph.add_edge("node1", "node2")
    assert await graph_storage.edge_exists({"sourceId": "node1"}, {"targetId": "node2"}) is True


@pytest.mark.asyncio
async def test_edge_exists_with_knwl_node():
    graph_storage = GraphStorage()
    node1 = KnwlNode(id="node1", name="node1")
    node2 = KnwlNode(id="node2", name="node2")
    graph_storage.graph.add_edge(node1.id, node2.id)
    assert await graph_storage.edge_exists(node1, node2)


@pytest.mark.asyncio
async def test_get_node_by_name():
    # Create a GraphStorage instance
    graph_storage = GraphStorage()

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
    graph_storage = GraphStorage()
    edges = await graph_storage.get_edges()
    assert edges == []


@pytest.mark.asyncio
async def test_get_edges_with_edges():
    graph_storage = GraphStorage()
    node1 = KnwlNode(id="1", name="Node 1")
    node2 = KnwlNode(id="2", name="Node 2")
    edge = KnwlEdge(sourceId="1", targetId="2", weight=1.0)

    await graph_storage.upsert_node(node1.id, node1)
    await graph_storage.upsert_node(node2.id, node2)
    await graph_storage.upsert_edge(edge.sourceId, edge.targetId, edge)

    edges = await graph_storage.get_edges()
    assert len(edges) == 1
    assert edges[0].sourceId == "1"
    assert edges[0].targetId == "2"
    assert edges[0].weight == 1.0


@pytest.mark.asyncio
async def test_get_edge_weight_existing_edge():
    graph_storage = GraphStorage()
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
    graph_storage = GraphStorage()
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
    graph_storage = GraphStorage()
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
    graph_storage = GraphStorage()
    source_node_id = "node1"
    target_node_id = "node2"
    weight = 3.5
    edge = KnwlEdge(sourceId=source_node_id, targetId=target_node_id, weight=weight)

    # Add nodes and edge to the graph
    await graph_storage.upsert_node(source_node_id, {"name": "Node 1"})
    await graph_storage.upsert_node(target_node_id, {"name": "Node 2"})
    await graph_storage.upsert_edge(source_node_id, target_node_id, asdict(edge))

    # Test get_edge_weight using KnwlEdge instance
    result = await graph_storage.get_edge_weight(edge)
    assert result == weight


@pytest.mark.asyncio
async def test_remove_edge_with_edge_object():
    graph_storage = GraphStorage()
    edge = KnwlEdge(sourceId="node1", targetId="node2", weight=1.0)
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge(edge)

    assert await graph_storage.edge_exists(edge)

    await graph_storage.remove_edge(edge)

    assert not await graph_storage.edge_exists(edge)


@pytest.mark.asyncio
async def test_remove_edge_with_tuple():
    graph_storage = GraphStorage()
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge("node1", "node2", KnwlEdge(sourceId="node1", targetId="node2", weight=1.0))

    assert await graph_storage.edge_exists("node1", "node2")

    await graph_storage.remove_edge(("node1", "node2"))

    assert not await graph_storage.edge_exists("node1", "node2")


@pytest.mark.asyncio
async def test_remove_edge_with_node_objects():
    graph_storage = GraphStorage()
    node1 = KnwlNode(id="node1", name="Node 1")
    node2 = KnwlNode(id="node2", name="Node 2")
    await graph_storage.upsert_node(node1.id, node1)
    await graph_storage.upsert_node(node2.id, node2)
    await graph_storage.upsert_edge(node1.id, node2.id, KnwlEdge(sourceId=node1.id, targetId=node2.id, weight=1.0))

    assert await graph_storage.edge_exists(node1.id, node2.id)

    await graph_storage.remove_edge(node1, node2)

    assert not await graph_storage.edge_exists(node1.id, node2.id)


@pytest.mark.asyncio
async def test_remove_edge_with_node_ids():
    graph_storage = GraphStorage()
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge("node1", "node2", KnwlEdge(sourceId="node1", targetId="node2", weight=1.0))

    assert await graph_storage.edge_exists("node1", "node2")

    await graph_storage.remove_edge("node1", "node2")

    assert not await graph_storage.edge_exists("node1", "node2")


@pytest.mark.asyncio
async def test_remove_edge_with_invalid_data():
    graph_storage = GraphStorage()
    await graph_storage.upsert_node("node1", KnwlNode(id="node1", name="Node 1"))
    await graph_storage.upsert_node("node2", KnwlNode(id="node2", name="Node 2"))
    await graph_storage.upsert_edge("node1", "node2", KnwlEdge(sourceId="node1", targetId="node2", weight=1.0))

    with pytest.raises(ValueError):
        await graph_storage.remove_edge("node1")


@pytest.mark.asyncio
async def test_get_nodes_empty_graph():
    storage = GraphStorage()
    nodes = await storage.get_nodes()
    assert nodes == []


@pytest.mark.asyncio
async def test_get_nodes_with_nodes():
    storage = GraphStorage()
    node1 = KnwlNode(name="Node1")
    node2 = KnwlNode(name="Node2")
    await storage.upsert_node(node1.id, node1)
    await storage.upsert_node(node2.id, node2)

    nodes = await storage.get_nodes()
    assert len(nodes) == 2
    assert any(node.id == node1.id and node.name == "Node1" for node in nodes)
    assert any(node.id == node2.id and node.name == "Node2" for node in nodes)

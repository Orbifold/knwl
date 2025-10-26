from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from knwl.models import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class DummyStrategy(GragStrategyBase):
    async def augment(self, input):
        return None


@pytest.mark.asyncio
async def test_semantic_nodes():
    grag = MagicMock()
    n1 = KnwlNode(
        id="node1",
        name="Node 1",
        type="A",
        description="Test node 1",
        index=1,
        degree=5,
    )
    n2 = KnwlNode(
        id="node2",
        name="Node 2",
        type="B",
        description="Test node 2",
        index=0,
        degree=10,
    )

    # mock the nearest_nodes method
    grag.nearest_nodes = AsyncMock(return_value=[n1, n2])
    # mock the get_node_by_id method
    grag.get_node_by_id = AsyncMock(side_effect=lambda x: n1 if x == "node1" else n2)
    # mock the node_degree method
    grag.node_degree = AsyncMock(
        side_effect=lambda x: n1.degree if x == "node1" else n2.degree
    )
    strategy = DummyStrategy(grag)
    nodes = await strategy.semantic_node_search("test query")
    assert len(nodes) == 2
    assert isinstance(nodes[0], KnwlNode)
    assert nodes[0].id == "node2"  # node with higher degree should be first

    grag.node_degree = AsyncMock(side_effect=lambda x: None)
    nodes = await strategy.semantic_node_search("test query")
    assert len(nodes) == 2  # node degree missing, but still returns nodes

    grag.nearest_nodes = AsyncMock(return_value=None)
    assert await strategy.semantic_node_search("test query") == None

    grag.nearest_nodes = AsyncMock(return_value=[])
    assert await strategy.semantic_node_search("test query") == None


@pytest.mark.asyncio
async def test_semantic_edges():
    grag = MagicMock()
    e1 = KnwlEdge(
        source_id="node1",
        target_id="node2",
        type="related_to",
        description="Edge 1",
        weight=2.0,
        degree=4,
    )
    e2 = KnwlEdge(
        source_id="node2",
        target_id="node3",
        type="known_for",
        description="Edge 2",
        weight=3.0,
        degree=6,
    )
    grag.nearest_edges = AsyncMock(return_value=[e1, e2])
    grag.edge_degree = AsyncMock(
        side_effect=lambda s, t: (
            e1.degree if (s, t) == ("node1", "node2") else e2.degree
        )
    )
    grag.get_node_by_id = AsyncMock(
        side_effect=lambda x: KnwlNode(
            id=x,
            name=f"node{x[-1]}",
            type="A",
            description=f"Test node {x[-1]}",
            index=int(x[-1]),
        )
    )

    strategy = DummyStrategy(grag)
    edges = await strategy.semantic_edge_search("test query")
    assert len(edges) == 2
    assert isinstance(edges[0], KnwlEdge)
    assert edges[0].source_name == "node2"  # edge with higher degree should be first
    assert edges[0].target_name == "node3"


@pytest.mark.asyncio
async def test_nodes_from_edges():
    grag = MagicMock()
    n1 = KnwlNode(
        id="node1",
        name="Node 1",
        type="A",
        description="Test node 1",
        index=1,
        degree=5,
    )
    n2 = KnwlNode(
        id="node2",
        name="Node 2",
        type="B",
        description="Test node 2",
        index=0,
        degree=10,
    )
    n3 = KnwlNode(
        id="node3",
        name="Node 3",
        type="C",
        description="Test node 3",
        index=0,
        degree=2,
    )
    e1 = KnwlEdge(
        source_id="node1",
        target_id="node2",
        type="related_to",
        description="Edge 1",
        weight=2.0,
    )
    e2 = KnwlEdge(
        source_id="node2",
        target_id="node3",
        type="related_to",
        description="Edge 2",
        weight=2.4,
    )
    node_map = {
        "node1": n1,
        "node2": n2,
        "node3": n3,
    }
    grag.get_node_by_id = AsyncMock(side_effect=lambda x: node_map.get(x))
    degrees = {"node1": 5, "node2": 10, "node3": 2}
    grag.node_degree = AsyncMock(side_effect=lambda x: degrees.get(x, 0))

    strategy = DummyStrategy(grag)
    nodes = await strategy.nodes_from_edges([e1])
    assert len(nodes) == 2
    assert isinstance(nodes[0], KnwlNode)
    assert nodes[0].id == "node2"  # node with higher degree should be first


@pytest.mark.asyncio
async def test_edges_from_nodes():
    grag = MagicMock()
    n1 = KnwlNode(
        id="node1",
        name="Node 1",
        type="A",
        description="Test node 1",
        index=1,
        degree=5,
    )
    n2 = KnwlNode(
        id="node2",
        name="Node 2",
        type="B",
        description="Test node 2",
        index=0,
        degree=10,
    )
    e1 = KnwlEdge(
        id="edge1",
        source_id="node1",
        target_id="node2",
        type="related_to",
        description="Edge 1",
        weight=2.0,
        degree=4,
    )
    e2 = KnwlEdge(
        id="edge2",
        source_id="node2",
        target_id="node3",
        type="known_for",
        description="Edge 2",
        weight=3.0,
        degree=6,
    )
    grag.get_attached_edges = AsyncMock(return_value=[e1, e2])
    grag.assign_edge_degrees = AsyncMock()
    grag.get_semantic_endpoints = AsyncMock(
        return_value={
            "edge1": ("node1", "node2"),
            "edge2": ("node2", "node3"),
        }
    )
    grag.get_node_by_id = AsyncMock(
        side_effect=lambda x: KnwlNode(
            id=x,
            name=f"node{x[-1]}",
            type="A",
            description=f"Test node {x[-1]}",
            index=int(x[-1]),
        )
    )

    strategy = DummyStrategy(grag)
    edges = await strategy.edges_from_nodes([n1, n2])
    assert len(edges) == 2
    assert isinstance(edges[0], KnwlEdge)
    assert edges[0].source_name == "node2"  # edge with higher degree should be first
    assert edges[0].target_name == "node3"
    assert edges[0].index == 0

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from knwl.models import KnwlDocument, KnwlEdge
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlText import KnwlText
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
        side_effect=lambda id: (
            e1.degree if id == "edge1" else e2.degree
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


@pytest.mark.asyncio
async def test_chunk_stats():
    grag = MagicMock()

    nodes = [
        KnwlNode(
            id="node1",
            name="Node 1",
            type="A",
            description="Test node 1",
            index=1,
            degree=5,
            chunk_ids=["chunk1", "chunk2", "chunk3"],
        ),
        KnwlNode(
            id="node2",
            name="Node 2",
            type="B",
            description="Test node 2",
            index=0,
            degree=10,
            chunk_ids=["chunk2", "chunk3", "chunk4"],
        ),
        KnwlNode(
            id="node3",
            name="Node 3",
            type="B",
            description="Test node 3",
            index=0,
            degree=7,
            chunk_ids=[],
        ),
    ]
    edge1 = KnwlEdge(
        id="edge1",
        source_id="node1",
        target_id="node2",
        type="related_to",
        description="Edge 1",
        weight=2.0,
    )
    edge2 = KnwlEdge(
        id="edge2",
        source_id="node2",
        target_id="node3",
        type="related_to",
        description="Edge 2",
        weight=2.4,
    )
    grag.get_attached_edges = AsyncMock(return_value=[edge1, edge2])
    grag.get_node_by_id = AsyncMock(
        side_effect=lambda x: next((n for n in nodes if n.id == x), None)
    )
    grag.get_semantic_endpoints = AsyncMock(
        return_value={
            "edge1": ("node1", "node2"),
            "edge2": ("node2", "node3"),
        }
    )
    strategy = DummyStrategy(grag)
    stats = await strategy.chunk_stats_from_nodes(nodes)
    assert stats == {
        "chunk2": 1,  # appears once in edge1 at both endpoints
        "chunk3": 1,  # appears once in edge2 at both endpoints
        "chunk1": 0,  # not common in any edge
        "chunk4": 0,
    }


@pytest.mark.asyncio
async def test_unique_chunks():
    nodes = [
        KnwlNode(
            id="node1",
            name="Node 1",
            type="A",
            description="Test node 1",
            index=1,
            degree=5,
            chunk_ids=["chunk1", "chunk2", "chunk3"],
        ),
        KnwlNode(
            id="node2",
            name="Node 2",
            type="B",
            description="Test node 2",
            index=0,
            degree=10,
            chunk_ids=["chunk2", "chunk3", "chunk4"],
        ),
        KnwlNode(
            id="node2",
            name="Node 2",
            type="B",
            description="Test node 2",
            index=0,
            degree=10,
            chunk_ids=[],
        ),
    ]
    ids = DummyStrategy.unique_chunk_ids(nodes)
    assert set(ids) == {"chunk1", "chunk2", "chunk3", "chunk4"}


@pytest.mark.asyncio
async def test_text_from_nodes():
    grag = MagicMock()

    chunk_map = {
        "chunk1": KnwlChunk(id="chunk1", content="This is chunk 1."),
        "chunk2": KnwlChunk(id="chunk2", content="This is chunk 2."),
        "chunk3": KnwlChunk(id="chunk3", content="This is chunk 3."),
    }

    grag.get_chunk_by_id = AsyncMock(side_effect=lambda x: chunk_map.get(x))

    strategy = DummyStrategy(grag)
    strategy.chunk_stats_from_nodes = AsyncMock(
        return_value={
            "chunk1": 1,
            "chunk2": 5,
            "chunk3": 2,
        }
    )
    texts = await strategy.texts_from_nodes(
        [{}, {}], params=MagicMock(return_chunks=True)
    )
    assert len(texts) == 3
    assert texts[0].id == "chunk2"  # highest count
    assert texts[0].text == "This is chunk 2."


@pytest.mark.asyncio
async def test_references():
    grag = MagicMock()
    texts = [
        KnwlText(id="t1", text="Text 1", index=2, origin_id="chunk1"),
        KnwlText(id="t2", text="Text 2", index=5, origin_id="chunk2"),
    ]
    grag.get_chunk_by_id = AsyncMock(
        side_effect=lambda x: (
            {"id": x, "content": f"Content for {x}"}
            if x in ["chunk1", "chunk2"]
            else None
        )
    )
    grag.get_source_by_id = AsyncMock(
        side_effect=lambda x: (
            KnwlDocument(
                id=f"Source of {x}",
                content=f"Content for {x}",
                name=f"Source for {x}",
                description="Desc",
                timestamp="now",
            )
            if x in ["chunk1", "chunk2"]
            else None
        )
    )
    strategy = DummyStrategy(grag)
    references = await strategy.references_from_texts(texts)
    assert len(references) == 2
    assert references[0].content == "Content for chunk1"
    assert references[0].document_id == "Source of chunk1"


@pytest.mark.asyncio
async def test_references_from_chunks():
    grag = MagicMock()
    chunk_map = {
        "chunk1": KnwlChunk(id="chunk1", content="This is chunk 1.", origin_id="Origin 1"),
        "chunk2": KnwlChunk(id="chunk2", content="This is chunk 2.", origin_id="Origin 2"),
        "chunk3": KnwlChunk(id="chunk3", content="This is chunk 3.", origin_id="Origin 3"),
    }

    grag.get_chunk_by_id = AsyncMock(side_effect=lambda x: chunk_map.get(x))
    grag.get_source_by_id = AsyncMock(
        side_effect=lambda x: (
            KnwlDocument(
                id=f"Document of {x}",
                content=f"Content of {x}",
                name=f"Source for {x}",
                description="Desc",
                timestamp="now",
            )
            if x in ["Origin 1", "Origin 2", "Origin 3"]
            else None
        )
    )
    strategy = DummyStrategy(grag)
    references = await strategy.references_from_texts(chunk_map.values())
    assert len(references) == 3
    assert references[0].content == "Content of Origin 1"

import pytest

from knwl.semantic.graph.semantic_graph import SemanticGraph
from tests.fixtures import random_edges, random_nodes
pytestmark=pytest.mark.llm

g = SemanticGraph()


@pytest.mark.asyncio
async def test_embeddings(random_nodes, random_edges):
    await g.embed_nodes(random_nodes)
    await g.embed_edges(random_edges)
    node1 = await g.get_node_by_id(random_nodes[0].id)
    assert node1 is not None
    edge1 = await g.get_edge_by_id(random_edges[0].id)
    assert edge1 is not None
    similar_edges = await g.get_similar_edges(random_edges[0], top_k=3)
    assert similar_edges is not None
    assert len(similar_edges) > 0

import uuid
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import KnwlDocument
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.utils import get_full_path
import os


@pytest.mark.asyncio
async def test_extraction():
    input = """Euler is credited with being the first to develop graph theory (partly as a solution for the problem of the Seven Bridges of Königsberg, which is also considered the first practical application of topology). He also became famous for, among many other accomplishments, solving several unsolved problems in number theory and analysis, including the famous Basel problem. Euler has also been credited for discovering that the sum of the numbers of vertices and faces minus the number of edges of a polyhedron that has no holes equals 2, a number now commonly known as the Euler characteristic. In physics, Euler reformulated Isaac Newton's laws of motion into new laws in his two-volume work Mechanica to better explain the motion of rigid bodies. He contributed to the study of elastic deformations of solid objects. Euler formulated the partial differential equations for the motion of inviscid fluid, and laid the mathematical foundations of potential theory."""
    doc = KnwlDocument(content=input, id=f"{str(uuid.uuid4())}.txt")
    graph = services.get_service("graph_rag")
    result = await graph.extract(doc, enable_chunking=False)
    assert result.input.content == input
    assert result.graph is not None
    assert "Euler" in result.graph.get_node_names()
    assert len(result.graph.nodes) > 0
    assert len(result.graph.edges) > 0
    print("")
    print_knwl(result)

    print("")
    for node in result.graph.nodes:
        print_knwl(node)

    for edge in result.graph.edges:
        print_knwl(edge)
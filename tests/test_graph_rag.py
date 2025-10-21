import uuid
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import KnwlDocument
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.utils import get_full_path
import os
from tests.fixtures import random_article

@pytest.mark.asyncio
async def test_extraction(random_article: str):
    content =await random_article
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    graph = services.get_service("graph_rag")
    result = await graph.extract(doc, enable_chunking=False)
    assert result.input.content == content
    assert result.graph is not None
    
    assert len(result.graph.nodes) > 0
    assert len(result.graph.edges) > 0
    print("")
    print_knwl(result)

    print("")
    for node in result.graph.nodes:
        print_knwl(node)

    for edge in result.graph.edges:
        print_knwl(edge)
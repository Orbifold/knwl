import uuid
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import GragParams, KnwlDocument, KnwlGragContext, KnwlGragInput
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.utils import get_full_path
import os

from tests.library.collect import get_library_article


@pytest.mark.asyncio
async def test_extraction():

    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag:GraphRAG = services.get_service("graph_rag")
    result = await grag.extract(doc, enable_chunking=False)
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

@pytest.mark.asyncio
async def test_augmentation():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag:GraphRAG = services.get_service("graph_rag")    
    await grag.ingest(doc)
    input = KnwlGragInput(
        text="Explain the concept of homeomorphism in topology.",
        name="Test Query",
        description="A test query for topology concepts.",
        params=GragParams(mode="local", top_k=5)
    )
    found = await grag.augment(input)
    print_knwl(found)
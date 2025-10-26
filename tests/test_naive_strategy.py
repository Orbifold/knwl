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
async def test_naive_augmentation():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)
    input = KnwlGragInput(
        text="Explain the concept of homeomorphism in topology.",
        name="Test Query",
        description="A test query for topology concepts.",
        params=GragParams(mode="naive", top_k=5),
    )
    found = await grag.augment(input)
    print("")
    print_knwl(found, show_chunks=True, show_nodes=False, show_edges=False)

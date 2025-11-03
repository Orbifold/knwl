import uuid
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import KnwlParams, KnwlDocument, KnwlContext, KnwlInput
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.semantic.graph_rag.strategies.hybrid_strategy import HybridGragStrategy
from knwl.semantic.graph_rag.strategies.local_strategy import LocalGragStrategy
from knwl.utils import get_full_path
pytestmark = pytest.mark.llm

from tests.library.collect import get_library_article


@pytest.mark.asyncio
async def test_from_article():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)
    input = KnwlInput(
        text="homeomorphism,topology",
        name="Test Query",
        description="A test query for topology concepts.",
        params=KnwlParams(
            strategy="hybrid",
            return_chunks=True,
        ),
    )
    strategy = HybridGragStrategy(grag)
    found = await strategy.augment(input)
    print("")
    print_knwl(found, show_texts=True, show_nodes=True, show_edges=True)

    assert found is not None
    assert isinstance(found, KnwlContext)
    assert len(found.texts) > 0
    assert len(found.nodes) > 0
    assert len(found.edges) > 0
    assert found.input == input

import uuid
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import KnwlParams, KnwlDocument, KnwlContext, KnwlInput
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.semantic.graph_rag.strategies.naive_strategy import NaiveGragStrategy
from knwl.utils import get_full_path
import os
pytestmark = pytest.mark.llm

from tests.library.collect import get_library_article


@pytest.mark.asyncio
async def test_naive_augmentation():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)
    input = KnwlInput(
        text="Explain the concept of homeomorphism in topology.",
        name="Test Query",
        description="A test query for topology concepts.",
        params=KnwlParams(strategy="naive"),
    )
    found = await grag.augment(input)
    print("")
    print_knwl(found, show_chunks=True, show_nodes=False, show_edges=False)

    """ 
    The above will render something like this:
    
╭───────────────────────────────── 🎯 Context ─────────────────────────────────╮
│                                                                              │
│                                                                              │
│  Question: Explain the concept of homeomorphism in topology.                 │
│                                                                              │
│                                                                              │
│ 📑 Chunks:                                                                   │
│                                                                              │
│ 📄[0] -to-one and onto, and if the inverse of the function is also           │
│ continuous, then the function is called a homeomorphism and the domain of    │
│ the function is...                                                           │
│                                                                              │
│                                                                              │
│ 📄[1] Topology (from the Greek words τόπος, 'place, location', and λόγος,    │
│ 'study') is the branch of mathematics concerned with the properties of a     │
│ geometric...                                                                 │
│                                                                              │
│                                                                              │
│ 📄[2] require distorting the space and affecting the curvature or volume.    │
│                                                                              │
│ Geometric topology                                                           │
│ Geometric topology is a branch of topology that primarily focu...            │
│                                                                              │
│                                                                              │
│ 📄[3] ic geometry. Donaldson, Jones, Witten, and Kontsevich have all won     │
│ Fields Medals for work related to topological field theory.                  │
│ The topological classif...                                                   │
│                                                                              │
│                                                                              │
│ 📄[4] en's theorem, covering spaces, and orbit spaces.)                      │
│ Wacław Sierpiński, General Topology, Dover Publications, 2000, ISBN          │
│ 0-486-41148-6                                                                │
│ Pickover, Clifford...                                                        │
│                                                                              │
│                                                                              │
╰───────────────────────── 5 chunks, 0 nodes, 0 edges ─────────────────────────╯
    """


@pytest.mark.asyncio
async def test_naive_augmentation():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)
    input = KnwlInput(
        text="Explain the concept of homeomorphism in topology.",
        name="Test Query",
        description="A test query for topology concepts.",
        params=KnwlParams(strategy="naive", return_chunks=True),
    )
    found = await grag.augment(input)
    print("")
    print_knwl(found, show_texts=True, show_nodes=False, show_edges=False)

    assert found is not None
    assert isinstance(found, KnwlContext)
    assert len(found.texts) > 0
    assert len(found.nodes) == 0
    assert len(found.edges) == 0
    assert found.input == input


@pytest.mark.asyncio
async def test_naive_strategy_initialization():
    """Test that NaiveGragStrategy can be initialized with a GraphRAG instance."""
    grag: GraphRAG = services.get_service("graph_rag")
    strategy = NaiveGragStrategy(grag)
    assert strategy.grag == grag


@pytest.mark.asyncio
async def test_naive_strategy_augment_with_no_results():
    """Test naive strategy when no chunks are found."""
    grag: GraphRAG = services.get_service("graph_rag")
    strategy = NaiveGragStrategy(grag)

    input = KnwlInput(
        text="A completely unrelated query that should find nothing",
        name="Empty Query",
        description="Test query that should return no results.",
        params=KnwlParams(strategy="naive", limit=5),
    )

    context = await strategy.augment(input)

    assert context is not None
    assert isinstance(context, KnwlContext)
    assert len(context.texts) == 0
    assert len(context.nodes) == 0
    assert len(context.edges) == 0
    assert context.input == input


@pytest.mark.asyncio
async def test_naive_strategy_augment_with_results():
    """Test naive strategy returns chunks in correct format."""
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)

    strategy = NaiveGragStrategy(grag)
    input = KnwlInput(
        text="topology",
        name="Test Query",
        description="Simple test query.",
        params=KnwlParams(strategy="naive", top_k=3),
    )

    context = await strategy.augment(input)

    assert context is not None
    assert isinstance(context, KnwlContext)
    assert len(context.texts) <= 3
    assert len(context.nodes) == 0
    assert len(context.edges) == 0

    # Verify chunk structure
    for i, chunk in enumerate(context.texts):
        assert chunk.text is not None
        assert chunk.id is not None
        assert chunk.index == i


@pytest.mark.asyncio
async def test_naive_strategy_respects_limit_param():
    """Test that naive strategy respects the limit parameter."""
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)

    strategy = NaiveGragStrategy(grag)

    # Test with limit=2
    input = KnwlInput(
        text="topology mathematics",
        name="Limited Query",
        description="Test query with limit.",
        params=KnwlParams(strategy="naive", top_k=2),
    )

    context = await strategy.augment(input)

    assert context is not None
    assert len(context.texts) <= 2

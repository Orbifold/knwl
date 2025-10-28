from unittest.mock import MagicMock
import uuid
import pytest

from knwl.format import print_knwl
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.semantic.graph_rag.strategies.keywords_strategy import KeywordsGragStrategy
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from unittest.mock import MagicMock, AsyncMock, patch
from knwl.models import (
    GragParams,
    KnwlDocument,
    KnwlGragContext,
    KnwlEdge,
    KnwlGragReference,
    KnwlGragText,
    KnwlNode,
    KnwlChunk,
)
from tests.library.collect import get_library_article
from knwl.services import services


@pytest.mark.asyncio
async def test_keywords_strategy():

    grag = MagicMock()

    strategy = KeywordsGragStrategy(grag)

    input = KnwlGragInput(
        text="keyword1, keyword2, keyword3",
        name="Test Keywords Input",
        description="A test input for keywords strategy.",
    )


@pytest.mark.asyncio
async def test_keywords_strategy_augment_success():
    grag = MagicMock()
    strategy = KeywordsGragStrategy(grag)

    # Mock data
    mock_edges = [
        KnwlEdge(id="edge1", source_id="node1", target_id="node2"),
        KnwlEdge(id="edge2", source_id="node2", target_id="node3"),
    ]
    mock_nodes = [
        KnwlNode(id="node1", name="Node 1"),
        KnwlNode(id="node2", name="Node 2"),
        KnwlNode(id="node3", name="Node 3"),
    ]
    mock_texts = [
        KnwlGragText(id="text1", content="Content for node1"),
        KnwlGragText(id="text2", content="Content for node2"),
    ]
    mock_references = [
        KnwlGragReference(
            id="ref1",
            document_id="d1",
        ),
        KnwlGragReference(id="ref2", document_id="d2"),
    ]

    # Mock async methods
    strategy.semantic_edge_search = AsyncMock(return_value=mock_edges)
    strategy.nodes_from_edges = AsyncMock(return_value=mock_nodes)
    strategy.texts_from_nodes = AsyncMock(return_value=mock_texts)
    strategy.references_from_chunks = AsyncMock(return_value=mock_references)

    input = KnwlGragInput(
        text="keyword1, keyword2, keyword3",
        name="Test Keywords Input",
        description="A test input for keywords strategy.",
    )

    result = await strategy.augment(input)

    assert isinstance(result, KnwlGragContext)
    assert result.input == input
    assert result.edges == mock_edges
    assert result.nodes == mock_nodes
    assert result.texts == mock_texts
    assert result.references == mock_references

    strategy.semantic_edge_search.assert_called_once_with(input)
    strategy.nodes_from_edges.assert_called_once_with(mock_edges)
    strategy.texts_from_nodes.assert_called_once_with(mock_nodes)
    strategy.references_from_chunks.assert_called_once_with(mock_texts)


@pytest.mark.asyncio
async def test_keywords_strategy_augment_whitespace_only():
    grag = MagicMock()
    strategy = KeywordsGragStrategy(grag)

    input = KnwlGragInput(
        text="   ,  ,   ",
        name="Whitespace Keywords Input",
        description="Input with only whitespace",
    )

    with pytest.raises(
        ValueError, match="KeywordsGragStrategy requires at least one keyword as input"
    ):
        await strategy.augment(input)


@pytest.mark.asyncio
async def test_keywords_strategy_augment_with_extra_spaces():
    grag = MagicMock()
    strategy = KeywordsGragStrategy(grag)

    mock_edges = []
    mock_nodes = []
    mock_texts = []
    mock_references = []

    strategy.semantic_edge_search = AsyncMock(return_value=mock_edges)
    strategy.nodes_from_edges = AsyncMock(return_value=mock_nodes)
    strategy.texts_from_nodes = AsyncMock(return_value=mock_texts)
    strategy.references_from_chunks = AsyncMock(return_value=mock_references)

    input = KnwlGragInput(
        text="k1,k2,k3",
        name="Spaces Keywords Input",
        description="Input with extra spaces",
    )

    result = await strategy.augment(input)

    assert isinstance(result, KnwlGragContext)
    strategy.semantic_edge_search.assert_called_once_with(input)
    strategy.nodes_from_edges.assert_called_once_with(mock_edges)
    strategy.texts_from_nodes.assert_called_once_with(mock_nodes)
    strategy.references_from_chunks.assert_called_once_with(mock_texts)


@pytest.mark.asyncio
async def test_from_article():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)
    input = KnwlGragInput(
        text="homeomorphism,topology",
        name="Test Query",
        description="A test query for topology concepts.",
        params=GragParams(
            mode="keywords",
            return_chunks=True,
        ),
    )
    strategy = KeywordsGragStrategy(grag)
    found = await strategy.augment(input)
    print("")
    print_knwl(found, show_texts=True, show_nodes=True, show_edges=True)

    assert found is not None
    assert isinstance(found, KnwlGragContext)
    assert len(found.texts) > 0
    assert len(found.nodes) > 0
    assert len(found.edges) == 5
    assert found.input == input

import pytest

from knwl.semantic.graph.semantic_graph import SemanticGraph


@pytest.mark.asyncio
async def test_service_basic():
    s = SemanticGraph()


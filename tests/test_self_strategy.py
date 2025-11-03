import pytest

from knwl.format import print_knwl
from knwl.models import KnwlInput, KnwlParams
from knwl.semantic.graph_rag.strategies.self_strategy import SelfGragStrategy
pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_self_strategy_augment():
    question = "What is the significance of DNA in living organisms?"
    strategy = SelfGragStrategy(grag=None)  # this strategy does not use grag in augment
    input = KnwlInput(text=question, params=KnwlParams(strategy="self", return_chunks=True))
    found = await strategy.augment(input)
    print("")
    print_knwl(found, show_texts=True, show_nodes=False, show_edges=False)

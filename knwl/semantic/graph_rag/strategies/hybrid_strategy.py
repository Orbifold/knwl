from typing import List

from knwl.logging import log
from knwl.models import (
    KnwlParams,
    KnwlEdge,
    KnwlContext,
    KnwlNode,
    KnwlText,
    KnwlReference,
)
from knwl.models.KnwlInput import KnwlInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.global_strategy import GlobalGragStrategy
from knwl.semantic.graph_rag.strategies.local_strategy import LocalGragStrategy
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.utils import unique_strings


class HybridGragStrategy(GragStrategyBase):
    """
    The hybrid stategy combines the global and the local strategies via low/high level keywords.
    This is the most expensive strategy, but also the most powerful one.
    """

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlInput) -> KnwlContext | None:
        keywords = await self.grag.extract_keywords(input.text)
        if not keywords:
            log.debug("No keywords found for global strategy.")
            return KnwlContext.empty(input)
        high_level = KnwlContext.empty(input)
        low_level = KnwlContext.empty(input)
        if len(keywords.high_level) > 0:
            high_level_query = ", ".join(keywords.high_level)
            input.text = high_level_query
            high_level = await self.augment_via_edges(input)
        if len(keywords.low_level) > 0:
            low_level_query = ", ".join(keywords.low_level)
            input.text = low_level_query
            low_level = await self.augment_via_nodes(input)
        return KnwlContext.combine(high_level, low_level)

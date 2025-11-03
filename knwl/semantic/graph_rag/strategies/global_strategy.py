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
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.utils import unique_strings


class GlobalGragStrategy(GragStrategyBase):

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlInput) -> KnwlContext | None:
        """
        The global strategy uses high-level keywords and semantic edge search based on these high-level keywords to find relevant nodes and edges.
        """
        keywords = await self.grag.extract_keywords(input.text)
        if not keywords:
            log.debug("No keywords found for global strategy.")
            return KnwlContext.empty(input)
        if len(keywords.high_level) == 0:
            log.debug("No high level keywords found for global strategy.")
            return KnwlContext.empty(input)
        input.text = ", ".join(
            keywords.high_level
        )  # Override input text with keywords for global topics
        return await self.augment_via_edges(input)

from typing import List

from knwl.logging import log
from knwl.models import (
    KnwlContext,
)
from knwl.models.KnwlInput import KnwlInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class LocalGragStrategy(GragStrategyBase):
    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlInput) -> KnwlContext | None:
        """
        The local strategy uses low-level keywords and semantic node search based on these low-level keywords to find relevant nodes and edges.
        """
        keywords = await self.grag.extract_keywords(input.text)
        if not keywords:
            log.debug("No keywords found for local strategy.")
            return KnwlContext.empty(input)
        if len(keywords.low_level) == 0:
            log.debug("No low level keywords found for local strategy.")
            return KnwlContext.empty(input)
        input.text = ", ".join(
            keywords.low_level
        )  # Override input text with keywords for local topics
        return await self.augment_via_nodes(input)

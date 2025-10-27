from typing import List

from knwl.logging import log
from knwl.models import (
    KnwlGragContext,
    KnwlGragText,
)
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class NaiveGragStrategy(GragStrategyBase):
    """
    This strategy does not use any graph-based augmentation. It simply returns the top-k chunk units.
    """

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None:
        """
        This is really just a redirect to the `nearest_chunks` method of the `RagBase` instance.
        Obviously, you don't need Knwl to do classic RAG but it's part of the framework so you can route or experiment with different strategies.
        """
        found = await self.grag.nearest_chunks(input.text, input.params)
        if found is None:
            found = []
        else:
            log.debug(
                f"NaiveGragStrategy.augment: found {len(found)} chunks for question '{input.text}'."
            )
            coll = []
            for i, chunk in enumerate(found):
                coll.append(
                    KnwlGragText(
                        text=chunk.content,
                        id=chunk.id,
                        origin_id=chunk.origin_id,
                        index=i,
                    )
                )
            found = coll
        context = KnwlGragContext(input=input, chunks=found, nodes=[], edges=[])
        return context

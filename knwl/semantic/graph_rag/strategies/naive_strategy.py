from typing import List

from knwl.logging import log
from knwl.models import (
    KnwlContext,
    KnwlText,
)
from knwl.models.KnwlInput import KnwlInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class NaiveGragStrategy(GragStrategyBase):
    """
    This strategy does not use any graph-based augmentation. It simply returns the top-k chunk units.
    """

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlInput) -> KnwlContext | None:
        """
        This is really just a redirect to the `nearest_chunks` method of the `RagBase` instance.
        Obviously, you don't need Knwl to do classic RAG but it's part of the framework so you can route or experiment with different strategies.
        Equally well, the chunks could be sorted based on how many nodes/edges they are connected to.
        """
        chunks = await self.grag.nearest_chunks(input.text, input.params)
        if chunks is None:
            return KnwlContext.empty(input)
        if input.params.return_chunks:            
            texts = await self.texts_from_chunks(chunks, params=input.params)
            references = await self.references_from_texts(texts)
        else:
            texts = []
            references = []
        return KnwlContext(
            input=input,
            texts=texts,
            nodes=[],
            edges=[],
            references=references,
        )

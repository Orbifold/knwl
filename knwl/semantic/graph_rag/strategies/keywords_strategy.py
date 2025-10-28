from typing import List

from knwl.logging import log
from knwl.models import (
    KnwlEdge,
    KnwlGragContext,
)
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class KeywordsGragStrategy(GragStrategyBase):

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None:
        if input.params.mode != "keywords":
            log.warn(
                "KeywordsGragStrategy requires 'keywords' mode, but proceeding anyway."
            )
        # the input is supposed to be an array of keywords in this case
        keywords = input.text.split(",")
        keywords = [kw.strip() for kw in keywords if len(kw.strip()) > 0]
        if not keywords or len(keywords) == 0:
            raise ValueError(
                "KeywordsGragStrategy requires at least one keyword as input"
            )
        log.debug(f"KeywordsGragStrategy: augmenting with keywords: {keywords}")

        edges: list[KnwlEdge] = await self.semantic_edge_search(input)
        if not edges or len(edges) == 0:
            return KnwlGragContext.empty(input=input)

        nodes = await self.nodes_from_edges(edges, sorted=True)
        if input.params.return_chunks:
            texts = await self.texts_from_nodes(nodes, params=input.params)
            references = await self.references_from_texts(texts)
        else:
            texts = []
            references = []
        context = KnwlGragContext(
            input=input,
            nodes=nodes,
            edges=edges,
            texts=texts,
            references=references,
        )
        return context

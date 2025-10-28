from typing import List

from knwl.logging import log
from knwl.models import (
    GragParams,
    KnwlEdge,
    KnwlGragContext,
    KnwlNode,
    KnwlGragText,
    KnwlGragReference,
)
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.utils import unique_strings


class GlobalGragStrategy(GragStrategyBase):

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None:
        keywords = await self.grag.extract_keywords(input.text)
        if not keywords:
            log.debug("No keywords found for global strategy.")
            return KnwlGragContext.empty(input)

        query = ", ".join(keywords.high_level)
        input.text = query  # Override input text with keywords for global topics
        nodes = await self.semantic_node_search(input)
        if not nodes:
            return KnwlGragContext.empty(input=input)
        edges = await self.edges_from_nodes(nodes)
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

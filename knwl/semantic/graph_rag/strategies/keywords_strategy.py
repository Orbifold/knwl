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


class KeywordsGragStrategy(GragStrategyBase):

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None:
        # the input is supposed to be an array of keywords in this case
        keywords = input.texts.split(",")
        keywords = [kw.strip() for kw in keywords]
        if not keywords or len(keywords) == 0:
            raise ValueError(
                "KeywordsGragStrategy requires at least one keyword as input"
            )
        log.debug(f"KeywordsGragStrategy: augmenting with keywords: {keywords}")

        # ====================== Primary Edges From Keywords ======================================
        # the edges across the whole KG where any of the keywords match
        edges: list[KnwlEdge] = await self.grag.nearest_edges(
            query=", ".join(keywords),
            query_param=input.params,
        )
        edges: List[KnwlGragEdge] = await self.sort_primary_edges(edges)

        # ====================== Nodes From Edges =================================================
        nodes = await self.get_nodes_from_edges(edges)

        # ====================== Chunks From Keywords =============================================
         

    

    async def get_rag_texts_from_edges(self, edges: list[KnwlEdge], query_param: GragParams, ) -> List[KnwlGragText]:
        stats = await self.create_chunk_stats_from_edges(edges)
        chunk_ids = unique_strings([e.chunkIds for e in edges])
        coll = []
        for i, chunk_id in enumerate(chunk_ids):
            chunk = await self.chunks_storage.get_by_id(chunk_id)
            coll.append(KnwlGragText(origin_id=str(i), index=stats[chunk_id], text=chunk["content"], id=chunk_id))

        coll = sorted(coll, key=lambda x: x.index, reverse=True)
        return coll
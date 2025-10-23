from typing import List

from knwl.logging import log
from knwl.models import (
    GragParams,
    KnwlEdge,
    KnwlGragContext,
    KnwlGragEdge,
    KnwlGragNode,
    KnwlNode,
    KnwlGragText,
    KnwlGragReference,
)
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.utils import unique_strings


class NaiveGragStrategy(GragStrategyBase):
    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None:

        

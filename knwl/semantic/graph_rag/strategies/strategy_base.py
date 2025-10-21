from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase


class GragStrategyBase:
    def __init__(self, grag: "GraphRAGBase"):
        self.grag = grag
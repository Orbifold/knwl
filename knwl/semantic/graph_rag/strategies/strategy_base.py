from abc import ABC, abstractmethod
from knwl.models import KnwlGragInput
from knwl.models.GragParams import GragParams
from knwl.models.KnwlGragContext import KnwlGragContext
from knwl.models.KnwlNode import KnwlNode
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.logging import log


class GragStrategyBase(ABC):
    def __init__(self, grag: "GraphRAGBase"):
        self.grag = grag

    @abstractmethod
    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None: ...

    async def get_primary_nodes(self, input: KnwlGragInput) -> list[KnwlNode] | None:
        """
        Asynchronously retrieves primary nodes based on a query and query parameters.
        This is essentially a basic RAG step over nodes.

        This function queries the node vectors to get the top-k nodes matching the query.
        It then retrieves the corresponding node data and node degrees from the graph storage.
        If any nodes are missing from the graph storage, a warning is logged.

        Args:
            query (str): The query string used to search for nodes.
            query_param (QueryParam): An object containing query parameters, including top_k.

        Returns:
            List[KnwlNode] | None: A list of KnwlNode objects if nodes are found, otherwise None.
        """
        query = input.text
        top_k = input.params.top_k
        # node rag: get top-k nodes
        found = await self.grag.nearest_nodes(query, top_k=top_k)
        if not len(found):
            return None
        # todo: translation from vector to node not necessary if the vector storage contains the data as well
        nodes = {}
        for n in found:
            node_data = await self.grag.get_node_by_id(n.id)
            if node_data is None:
                log.warning(
                    f"get_primary_nodes: node data not found for node Id: {n.id}"
                )
                continue
            else:
                nodes[n.id] = node_data

        # degree might also come in one go
        for n in found:
            degree = await self.grag.node_degree(n.id)
            if degree is None:
                log.warning(
                    f"get_primary_nodes: node degree not found for node Id: {n.id}"
                )
                continue
            else:
                if n.id in nodes:
                    # KnwlNodes are immutable, so we need to create a new instance with updated data
                    nodes[n.id] = nodes[n.id].update(data={"degree": degree})

        return nodes.values()

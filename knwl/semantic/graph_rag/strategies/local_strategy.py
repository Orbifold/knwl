from knwl.models import GragParams, KnwlContext, KnwlContextEdge, KnwlContextNode, KnwlNode
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class LocalGragStrategy(GragStrategyBase):
    """
    Executes a local query and returns the response.
    The local query takes the neighborhood of the hit nodes and uses the low-level keywords to find the most related text units.

    This method performs the following steps:
    1. Extracts keywords from the given query using a predefined prompt.
    2. Attempts to parse the extracted keywords from the result.
    3. If parsing fails, attempts to clean and re-parse the result.
    4. Retrieves context based on the extracted keywords and query parameters.
    5. Constructs a system prompt using the retrieved context and query parameters.
    6. Executes the query with the constructed system prompt and returns the response.

    Args:
        query (str): The query string to be processed.
        query_param (QueryParam): An object containing parameters for the query.

    Returns:
        str: The response generated from the query. If an error occurs during processing, a failure response is returned.
    """

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def get_context(
        self, query: str, query_param: GragParams
    ) -> KnwlContext | None:
        """
        This really is the heart of the whole GraphRAG intelligence.

        Asynchronously retrieves the local query context based on the provided query and query parameters.

        This function performs the following steps:
        1. Queries the node vectors to get the top-k nodes based on the query.
        2. Retrieves node data for the top-k nodes from the graph storage.
        3. Logs a warning if some nodes are missing, indicating potential storage damage or sync issues.
        4. Retrieves node degrees for the top-k nodes.
        5. Finds the most related text units and edges from the entities.
        6. Logs the number of entities, relations, and text units used in the local query.
        7. Converts the entities, relations, and text units into CSV format.
        8. Returns a formatted string containing the entities, relationships, and sources in CSV format.

        Args:
            query (str): The query string to search for.
            query_param (QueryParam): The parameters for the query, including the top_k value.

        Returns:
            str: A formatted string containing the entities, relationships, and sources in CSV format, or None if no results are found.
        """
        primary_nodes = await self.get_primary_nodes(query, query_param)
        if primary_nodes is None:
            return None
        # chunk texts in descending order of importance
        use_texts = await self.get_rag_texts_from_nodes(primary_nodes)
        # the relations with endpoint names in descending order of importance
        use_relations = await self.get_graph_rag_relations(primary_nodes, query_param)

        # ====================== Primary Nodes ==================================
        node_recs = []
        for i, n in enumerate(primary_nodes):
            node_recs.append(
                KnwlContextNode(
                    id=n.id,
                    index=str(i),
                    name=n.name,
                    type=n.type,
                    description=n.description,
                    order=n.degree,
                )
            )

        # ====================== Relations ======================================
        edge_recs = []
        for i, e in enumerate(use_relations):
            edge_recs.append(
                KnwlContextEdge(
                    id=e.id,
                    index=str(i),
                    source=e.source,
                    target=e.target,
                    description=e.description,
                    keywords=e.keywords,
                    weight=e.weight,
                    order=e.order,
                )
            )

        # ====================== Chunks ========================================
        chunk_recs = []
        for i, t in enumerate(use_texts):
            chunk_recs.append(
                KnwlRagChunk(id=t.id, index=str(i), text=t.text, order=t.order)
            )

        # ====================== References ====================================
        refs = await self.get_references([c.id for c in use_texts])

        return KnwlContext(
            nodes=node_recs, edges=edge_recs, chunks=chunk_recs, references=refs
        )

    async def get_primary_nodes(
        self, query: str, query_param: GragParams
    ) -> list[KnwlNode] | None:
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
            List[KnwlDegreeNode] | None: A list of KnwlDegreeNode objects if nodes are found,
                                         otherwise None.
        """
        # node rag: get top-k nodes
        found = await self.node_vectors.query(query, top_k=query_param.top_k)
        if not len(found):
            return None
        # todo: translation from vector to node not necessary if the vector storage contains the data as well
        node_datas = await asyncio.gather(
            *[self.graph_storage.get_node_by_id(r["id"]) for r in found]
        )

        # if the node vector exists but the node isn't in the graph, it's likely that the storage is damaged or not in sync
        if not all([n is not None for n in node_datas]):
            logger.warning("Some nodes are missing, maybe the storage is damaged")
        # degree might also come in one go
        node_degrees = await asyncio.gather(
            *[self.graph_storage.node_degree(r["name"]) for r in found]
        )
        nodes = [
            KnwlDegreeNode(degree=d, **n.model_dump(mode="json"))
            for k, n, d in zip(found, node_datas, node_degrees)
            if n is not None
        ]
        return nodes

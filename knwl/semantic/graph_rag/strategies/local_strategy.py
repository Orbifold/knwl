from typing import List

from knwl.logging import log
from knwl.models import GragParams, KnwlEdge, KnwlGragContext, KnwlGragEdge, KnwlGragNode, KnwlNode, KnwlGragText, KnwlGragReference
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.utils import unique_strings


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

    async def get_source_references(self, texts: List[KnwlGragText]) -> List[KnwlGragReference]:
        if not texts:
            return []
        refs = []
        for i, c in enumerate(texts):
            chunk_id = c.id
            chunk = await self.grag.get_chunk_by_id(chunk_id)
            if chunk is None:
                log.warn(f"Could not find chunk {chunk_id}")
                continue
            origin_id = chunk.origin_id
            if origin_id is None:
                log.warn(f"Could not find origin id for chunk {chunk_id}")
                continue
            doc = await self.grag.get_source_by_id(origin_id)
            if doc is None:
                log.warn(f"Could not find origin id for chunk {chunk_id}")
            refs.append(KnwlGragReference(id=origin_id, index=str(i), description=doc.description, name=doc.name, timestamp=doc.timestamp))
        return refs

    async def get_texts_from_nodes(self, primary_nodes: list[KnwlNode], params: GragParams) -> list[KnwlGragText]:
        """
        Returns the most relevant paragraphs based on the given primary nodes.
        What makes the paragraphs relevant is defined in the `create_chunk_stats_from_nodes` method.

        This method first creates chunk statistics for the provided primary nodes, then retrieves the corresponding text
        for each chunk from the chunk storage. The chunks are then sorted in decreasing order of their count.

        Args:
            primary_nodes (list[KnwlNode]): A list of primary nodes for which to retrieve the graph RAG texts.

        Returns:
            list[dict]: A list of dictionaries, each containing 'count' and 'text' keys, sorted in decreasing order of count.
        """
        stats = await self.create_chunk_stats_from_nodes(primary_nodes)
        graph_rag_chunks = {}
        for i, v in enumerate(stats.items()):
            chunk_id, count = v
            if params.return_chunks:
                chunk = await self.grag.get_chunk_by_id(chunk_id)
                if chunk is not None:
                    graph_rag_chunks[chunk_id] = KnwlGragText(order=count, text=chunk["content"], index=str(i), id=chunk_id)
            else:
                graph_rag_chunks[chunk_id] = KnwlGragText(order=count, text=None, index=str(i), id=chunk_id)
        # in decreasing order of count
        rag_texts = sorted(graph_rag_chunks.values(), key=lambda x: x.order, reverse=True)
        return rag_texts

    @staticmethod
    def get_chunk_ids(nodes: list[KnwlNode] | list[KnwlEdge]) -> list[str]:
        if nodes is None:
            raise ValueError("get_chunk_ids: parameter is None")
        if not len(nodes):
            return []
        lists = [n.chunk_ids for n in nodes]
        # flatten the list and remove duplicates
        return unique_strings(lists)

    async def get_attached_edges(self, nodes: List[KnwlNode]) -> List[KnwlEdge]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (List[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            List[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])

        return await self.grag.get_attached_edges(nodes)

    async def create_chunk_stats_from_nodes(self, primary_nodes: list[KnwlNode]) -> dict[str, int]:
        """

        This returns for each chunk id in the given primary nodes, how many times it appears in the edges attached to the primary nodes.
        In essence, a chunk is more important if this chunk has many relations between entities within the chunk.
        One could also count the number of nodes present in a chunk as a measure but the relationship is an even stronger indicator of information.

        This method calculates the number of times each chunk appears in the edges attached to the primary nodes.

        Args:
            primary_nodes (List[KnwlNode]): A list of primary nodes to analyze.

        Returns:
            dict[str, int]: A dictionary where the keys are chunk Id's and the values are the counts of how many times each chunk appears in the edges.
        """
        primary_chunk_ids = LocalGragStrategy.get_chunk_ids(primary_nodes)
        if not len(primary_chunk_ids):
            return {}
        all_edges = await self.get_attached_edges(primary_nodes)
        node_map = {n.id: n for n in primary_nodes}
        edge_chunk_ids = {}
        stats = {}
        for edge in all_edges:
            if edge.source_id not in node_map:
                node_map[edge.source_id] = await self.grag.get_node_by_id(edge.source_id)
            if edge.target_id not in node_map:
                node_map[edge.target_id] = await self.grag.get_node_by_id(edge.target_id)
            # take the chunkId's of the endpoints
            source_chunks = node_map[edge.source_id].chunk_ids
            target_chunks = node_map[edge.target_id].chunk_ids
            common_chunk_ids = list(set(source_chunks).intersection(target_chunks))
            edge_chunk_ids[edge.id] = common_chunk_ids
        for chunk_id in primary_chunk_ids:
            # count how many times this chunk appears in the edge_chunk_ids
            stats[chunk_id] = sum([chunk_id in v for v in edge_chunk_ids.values()])
        return stats

    async def get_graph_rag_relations(self, node_datas: list[KnwlNode], query_param: GragParams) -> List[KnwlGragEdge]:
        all_attached_edges = await self.get_attached_edges(node_datas)
        all_edges_degree = await self.grag.edge_degrees(all_attached_edges)
        all_edge_ids = unique_strings([e.id for e in all_attached_edges])
        edge_endpoint_names = await self.grag.get_semantic_endpoints(all_edge_ids)
        all_edges_data = []
        for i, v in enumerate(zip(all_attached_edges, all_edges_degree)):
            e, d = v
            if e is not None:
                all_edges_data.append(KnwlGragEdge(order=d, source=edge_endpoint_names[e.id][0], target=edge_endpoint_names[e.id][1], keywords=e.keywords, description=e.description, weight=e.weight, id=e.id, index=str(i)))
        # sort by edge degree and weight descending
        all_edges_data = sorted(all_edges_data, key=lambda x: (x.order, x.weight), reverse=True)
        return all_edges_data

    async def augment(self, input: KnwlGragInput) -> KnwlGragContext | None:
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

        primary_nodes = await self.get_primary_nodes(input)
        if not primary_nodes:
            return None

        # chunk texts in descending order of importance
        rag_texts = await self.get_texts_from_nodes(primary_nodes, input.params)
        # the relations with endpoint names in descending order of importance
        use_relations = await self.get_graph_rag_relations(primary_nodes, input.params)

        # ====================== Primary Nodes ==================================
        node_recs = []
        for i, n in enumerate(primary_nodes):
            node_recs.append(KnwlGragNode(id=n.id, index=str(i), name=n.name, type=n.type, description=n.description, order=n.data.get("degree"), ))

        # ====================== Relations ======================================
        edge_recs = use_relations

        # ====================== Chunks ========================================
        chunk_recs = rag_texts

        # ====================== References ====================================
        if input.params.return_references:
            refs = await self.get_source_references(rag_texts)
        else:
            refs = []

        return KnwlGragContext(input=input, nodes=node_recs, edges=edge_recs, chunks=chunk_recs, references=refs)

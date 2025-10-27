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

    async def get_source_references(
        self, texts: List[KnwlGragText]
    ) -> List[KnwlGragReference]:
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
            refs.append(
                KnwlGragReference(
                    id=origin_id,
                    index=str(i),
                    description=doc.description,
                    name=doc.name,
                    timestamp=doc.timestamp,
                )
            )
        return refs

    async def texts_from_nodes(
        self, primary_nodes: list[KnwlNode], params: GragParams
    ) -> list[KnwlGragText]:
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
        stats = await self.chunk_stats(primary_nodes)
        graph_rag_chunks = {}
        for i, v in enumerate(stats.items()):
            chunk_id, count = v
            if params.return_chunks:
                chunk = await self.grag.get_chunk_by_id(chunk_id)
                if chunk is not None:
                    graph_rag_chunks[chunk_id] = KnwlGragText(
                        index=count,
                        text=chunk["content"],
                        origin_id=str(i),
                        id=chunk_id,
                    )
            else:
                graph_rag_chunks[chunk_id] = KnwlGragText(
                    index=count, text=None, origin_id=str(i), id=chunk_id
                )
        # in decreasing order of count
        rag_texts = sorted(
            graph_rag_chunks.values(), key=lambda x: x.index, reverse=True
        )
        return rag_texts

   

    
    async def get_graph_rag_relations(
        self, node_datas: list[KnwlNode], query_param: GragParams
    ) -> List[KnwlEdge]:
        all_attached_edges = await self.edges_from_nodes(node_datas)
        all_edges_degree = await self.grag.assign_edge_degrees(all_attached_edges)
        all_edge_ids = unique_strings([e.id for e in all_attached_edges])
        edge_endpoint_names = await self.grag.get_semantic_endpoints(all_edge_ids)
        all_edges_data = []
        for i, v in enumerate(zip(all_attached_edges, all_edges_degree)):
            e, d = v
            if e is not None:
                all_edges_data.append(
                    KnwlEdge(
                        order=d,
                        source_name=edge_endpoint_names[e.id][0],
                        target=edge_endpoint_names[e.id][1],
                        keywords=e.keywords,
                        description=e.description,
                        weight=e.weight,
                        id=e.id,
                        index=str(i),
                    )
                )
        # sort by edge degree and weight descending
        all_edges_data = sorted(
            all_edges_data, key=lambda x: (x.index, x.weight), reverse=True
        )
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

        primary_nodes = await self.semantic_node_search(input)
        if not primary_nodes:
            return None

        # chunk texts in descending order of importance
        rag_texts = await self.texts_from_nodes(primary_nodes, input.params)
        # the relations with endpoint names in descending order of importance
        use_relations = await self.get_graph_rag_relations(primary_nodes, input.params)

        # ====================== Primary Nodes ==================================
        node_recs = []
        for i, n in enumerate(primary_nodes):
            node_recs.append(
                KnwlNode(
                    id=n.id,
                    index=str(i),
                    name=n.name,
                    type=n.type,
                    description=n.description,
                    order=n.degree,
                )
            )

        # ====================== Relations ======================================
        edge_recs = use_relations

        # ====================== Chunks ========================================
        chunk_recs = rag_texts

        # ====================== References ====================================
        if input.params.return_references:
            refs = await self.get_source_references(rag_texts)
        else:
            refs = []

        return KnwlGragContext(
            input=input,
            nodes=node_recs,
            edges=edge_recs,
            chunks=chunk_recs,
            references=refs,
        )

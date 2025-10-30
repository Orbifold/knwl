from abc import ABC, abstractmethod

from knwl.models import (
    KnwlEdge,
    KnwlEdge,
    KnwlInput,
    KnwlReference,
    KnwlText,
    KnwlNode,
)
from knwl.models.KnwlParams import KnwlParams
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlContext import KnwlContext
from knwl.models.KnwlNode import KnwlNode
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.logging import log
from knwl.utils import unique_strings


class GragStrategyBase(ABC):
    def __init__(self, grag: "GraphRAGBase"):
        self.grag = grag

    @abstractmethod
    async def augment(self, input: KnwlInput) -> KnwlContext | None:
        """
        You can find nearest nodes, edges, chunks, nodes from edges, edges from nodes...there is no single best approach within GRAG.
        A strategy refers to one way of augmenting the input one or more of these elements.
        To some extend you could also have strategies during ingestion, skipping certain elements or adding others. The Knwl framework is flexible enough to allow this but the default implementation ingests all elements while giving a handful of augmentation strategies.
        """
        ...

    async def semantic_node_search(
        self, input: KnwlInput | str
    ) -> list[KnwlNode] | None:
        """
        Retrieves the nearest nodes from the graph based on semantic similarity of the input.
        This is essentially a RAG step over nodes via the embedding of the nodes.

        The degree of the nodes is added which can be used for ranking of the nodes later on.

        Args:
            query (str): The query string used to search for nodes.
            query_param (QueryParam): An object containing query parameters, including top_k.

        Returns:
            list[KnwlNode] | None: A list of KnwlNode objects if nodes are found, otherwise None.
        """
        if isinstance(input, str):
            input = KnwlInput(text=input, params=KnwlParams())
        query = input.text
        # node rag: get top-k nodes
        found = await self.grag.nearest_nodes(query, input.params)
        if not found:
            return None
        # todo: translation from vector to node not necessary if the vector storage contains the data as well
        nodes_map = {}
        for n in found:
            node_data = await self.grag.get_node_by_id(n.id)
            if node_data is None:
                log.warning(
                    f"get_primary_nodes: node data not found for node Id: {n.id}"
                )
                continue
            else:
                nodes_map[n.id] = node_data

        # degree might also come in one go
        for n in found:
            degree = await self.grag.node_degree(n.id)
            if degree is None:
                log.warning(
                    f"get_primary_nodes: node degree not found for node Id: {n.id}"
                )
                continue
            else:
                if n.id in nodes_map:
                    # KnwlNodes are immutable, so we need to create a new instance with updated data
                    nodes_map[n.id].degree = degree

        # sort by degree descending and assign the index accordingly
        coll = []
        sorted_nodes = sorted(nodes_map.values(), key=lambda x: x.degree, reverse=True)
        for i, n in enumerate(sorted_nodes):
            kn = KnwlNode(
                type=n.type,
                id=n.id,
                description=n.description,
                name=n.name,
                order=n.degree,
                index=i,
                chunk_ids=n.chunk_ids,
            )
            coll.append(kn)
        return coll

    async def semantic_edge_search(
        self, input: KnwlInput | str
    ) -> list[KnwlEdge] | None:
        """
        Retrieves the nearest edges from the graph based on semantic similarity of the input.
        This is essentially a RAG step over edges via the embedding of the edges.

        Args:
            query (str): The query string used to search for edges.
            query_param (QueryParam): An object containing query parameters, including top_k.
        Returns:
            list[KnwlEdge] | None: A list of KnwlEdge objects if edges are found, otherwise None.
        """
        if isinstance(input, str):
            input = KnwlInput(text=input, params=KnwlParams())
        query = input.text
        # edge rag: get top-k nodes
        edges: list[KnwlEdge] = await self.grag.nearest_edges(
            query=query, params=input.params
        )
        for e in edges:
            e.degree = await self.grag.edge_degree(e.id)

        sorted_edges = sorted(edges, key=lambda x: (x.degree, x.weight), reverse=True)
        edge_endpoint_ids = unique_strings(
            [e.source_id for e in edges] + [e.target_id for e in edges]
        )
        edge_endpoint_names = await self.node_id_to_name_map(edge_endpoint_ids)
        all_edges_data = []
        for i, e in enumerate(sorted_edges):
            if e is not None:
                all_edges_data.append(
                    KnwlEdge(
                        degree=e.degree,
                        source_name=edge_endpoint_names[e.source_id],
                        target_name=edge_endpoint_names[e.target_id],
                        target=edge_endpoint_names[e.target_id],
                        source_id=e.source_id,
                        target_id=e.target_id,
                        keywords=e.keywords,
                        description=e.description,
                        weight=e.weight,
                        id=e.id,
                        index=i,
                        type=e.type,
                        chunk_ids=e.chunk_ids,
                    )
                )
        # sorted by degree and weight descending
        return all_edges_data

    async def node_id_to_name_map(self, node_ids: list[str]) -> dict[str:str]:
        """
        Maps node Id's to their corresponding names.
        """
        mapping = {}
        for node_id in node_ids:
            node = await self.grag.get_node_by_id(node_id)
            mapping[node_id] = node.name
        return mapping

    async def nodes_from_edges(
        self, edges: list[KnwlEdge], sorted: bool = True
    ) -> list[KnwlNode]:
        """
        Returns the endpoint nodes of the given edges in descending order of their degree if sorted is True.
        """

        node_ids = unique_strings(
            [e.source_id for e in edges] + [e.target_id for e in edges]
        )
        all_nodes = []
        for node_id in node_ids:
            n = await self.grag.get_node_by_id(node_id)
            if n is None:
                continue
            if sorted:
                degree = await self.grag.node_degree(node_id)
            else:
                degree = 0
            all_nodes.append(
                KnwlNode(
                    id=n.id,
                    name=n.name,
                    type=n.type,
                    description=n.description,
                    chunk_ids=n.chunk_ids,
                    degree=degree,
                    index=0,
                )
            )
        all_nodes.sort(key=lambda x: x.degree, reverse=True)
        # set index
        for i, n in enumerate(all_nodes):
            n.index = i
        return all_nodes

    async def edges_from_nodes(
        self, nodes: list[KnwlNode], sorted: bool = True
    ) -> list[KnwlEdge]:
        """
        Collects edges attached to the given nodes and optionally sorts them by degree and weight in descending order.

        Args:
            nodes (list[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])

        if not all([isinstance(n, KnwlNode) for n in nodes]):
            raise ValueError("get_attached_edges: all items in nodes must be KnwlNode")
        edges = await self.grag.get_attached_edges(nodes)
        if sorted:
            await self.grag.assign_edge_degrees(edges)
        all_edge_ids = unique_strings([e.id for e in edges])
        edge_endpoint_names = await self.grag.get_semantic_endpoints(all_edge_ids)
        for e in edges:
            e.source_name = edge_endpoint_names[e.id][0]
            e.target_name = edge_endpoint_names[e.id][1]

        # sort by edge degree and weight descending
        if sorted:
            edges.sort(key=lambda x: (x.degree, x.weight), reverse=True)
            # set index
            for i, e in enumerate(edges):
                e.index = i
        return edges

    async def chunk_stats_from_nodes(self, nodes: list[KnwlNode]) -> dict[str, int]:
        """
        This returns for each chunk id in the given primary nodes, how many times it appears in the edges attached to the primary nodes.
        In essence, a chunk is more important if this chunk has many relations between entities within the chunk.
        One could also count the number of nodes present in a chunk as a measure but the relationship is an even stronger indicator of information.

        Args:
            primary_nodes (list[KnwlNode]): A list of primary nodes to analyze.

        Returns:
            dict[str, int]: A dictionary where the keys are chunk Id's and the values are the counts of how many times each chunk appears in the edges.
        """
        chunk_ids = self.unique_chunk_ids(nodes)  # chunk ids across all given nodes
        if not len(chunk_ids):
            return {}
        all_edges = await self.edges_from_nodes(nodes, sorted=False)
        node_map = {n.id: n for n in nodes}  # node id -> KnwlNode
        edge_chunk_ids = {}  # edge id -> list of chunk ids in both endpoints
        stats = {}  # chunk id -> count of appearances in edges
        for edge in all_edges:
            if edge.source_id not in node_map:
                node_map[edge.source_id] = await self.grag.get_node_by_id(
                    edge.source_id
                )
            if edge.target_id not in node_map:
                node_map[edge.target_id] = await self.grag.get_node_by_id(
                    edge.target_id
                )
            # take the chunkId's of the endpoints
            source_chunks = node_map[edge.source_id].chunk_ids
            target_chunks = node_map[edge.target_id].chunk_ids
            common_chunk_ids = list(set(source_chunks).intersection(target_chunks))
            edge_chunk_ids[edge.id] = common_chunk_ids
        for chunk_id in chunk_ids:
            # count how many times this chunk appears in the edge_chunk_ids
            stats[chunk_id] = sum([chunk_id in v for v in edge_chunk_ids.values()])
        return stats

    async def chunk_stats_from_edges(self, edges: list[KnwlEdge]) -> dict[str, int]:
        """
        This returns for each chunk id in the given edges, how many times it appears across the edges.
        In essence, a chunk is more important if this chunk has many relations between entities within the chunk.
        One could also count the number of nodes present in a chunk as a measure but the relationship is an even stronger indicator of information.

        Args:
            edges (list[KnwlEdge]): A list of edges to analyze.
        Returns:
            dict[str, int]: A dictionary where the keys are chunk Id's and the values are the counts of how many times each chunk appears in the edges.
        """
        stats = {}
        for edge in edges:
            for chunk_id in edge.chunk_ids:
                stats[chunk_id] = stats.get(chunk_id, 0) + 1
        return stats

    async def texts_from_nodes(
        self, nodes: list[KnwlNode], params: KnwlParams
    ) -> list[KnwlText]:
        """
        Returns the most relevant paragraphs based on the given nodes.
        What makes the paragraphs relevant is defined in the `chunk_stats` method.

        This method first creates chunk statistics for the provided nodes, then retrieves the corresponding text
        for each chunk from the chunk storage. The chunks are then sorted in decreasing order of their count.

        Args:
            primary_nodes (list[KnwlNode]): A list of primary nodes for which to retrieve the graph RAG texts.

        Returns:
            list[dict]: A list of dictionaries, each containing 'count' and 'text' keys, sorted in decreasing order of count.
        """
        if nodes is None or not len(nodes):
            return []
        stats = await self.chunk_stats_from_nodes(nodes)
        graph_rag_chunks = {}
        for i, v in enumerate(stats.items()):
            chunk_id, count = v
            if params.return_chunks:
                chunk = await self.grag.get_chunk_by_id(chunk_id)
                if chunk is not None:
                    graph_rag_chunks[chunk_id] = KnwlText(
                        index=count,
                        text=chunk.content,
                        origin_id=chunk.origin_id,
                        id=chunk_id,
                    )
            else:
                graph_rag_chunks[chunk_id] = KnwlText(
                    index=count, text=None, origin_id=None, id=chunk_id
                )
        # in decreasing order of count
        rag_texts = sorted(
            graph_rag_chunks.values(), key=lambda x: x.index, reverse=True
        )
        return rag_texts

    async def references_from_texts(
        self, texts: list[KnwlText] | list[KnwlChunk]
    ) -> list[KnwlReference]:
        """
        Returns references for the given texts by looking up their origin ids in the source storage.
        """
        if not texts:
            return []
        refs = []
        for i, c in enumerate(texts):
            origin_id = c.origin_id
            if origin_id is None:
                log.warn(f"Could not find origin id for text {c.id}")
                continue
            doc = await self.grag.get_source_by_id(origin_id)
            if doc is None:
                log.warn(f"Could not find source for text {c.id}")
            else:
                refs.append(
                    KnwlReference(
                        document_id=doc.id if doc else "",
                        index=i,
                        description=doc.description,
                        content=doc.content,
                        timestamp=doc.timestamp,
                    )
                )
        return refs

    async def text_from_edges(
        self, edges: list[KnwlEdge], query_param: KnwlParams
    ) -> list[KnwlText]:

        if edges is None or not len(edges):
            return []
        stats = await self.chunk_stats_from_edges(edges)
        chunk_ids = unique_strings([e.chunk_ids for e in edges])
        coll = []
        for i, chunk_id in enumerate(chunk_ids):
            chunk = await self.grag.get_chunk_by_id(chunk_id)
            coll.append(
                KnwlText(
                    origin_id=chunk_id, index=stats[chunk_id], text=chunk.content
                )
            )

        coll = sorted(coll, key=lambda x: x.index, reverse=True)
        return coll
    
    async def texts_from_chunks(
        self, chunks: list[KnwlChunk], params: KnwlParams
    ) -> list[KnwlText]:
        """
        Converts a list of KnwlChunk objects to KnwlGragText objects.
        The chunks could be sorted based on how many nodes/edges they are connected to, but this is not done here.
        
        Args:
            chunks (list[KnwlChunk]): A list of KnwlChunk objects to convert.

        Returns:
            list[KnwlGragText]: A list of KnwlGragText objects.
        """
        if chunks is None or not len(chunks):
            return []
        texts = []
        for i, chunk in enumerate(chunks):
            texts.append(
                KnwlText(
                    index=i,
                    text=chunk.content if params.return_chunks else None,
                    origin_id=chunk.origin_id,
                    id=chunk.id,
                )
            )
        return texts
    
    async def augment_via_nodes(self, input: KnwlInput) -> KnwlContext | None:
        """
        A strategy on its own, if you wish, to augment the input via nodes and through this retrieve edges, texts and references.
        """
        nodes = await self.semantic_node_search(input)
        if not nodes:
            return KnwlContext.empty(input=input)
        edges = await self.edges_from_nodes(nodes)
        if input.params.return_chunks:
            texts = await self.texts_from_nodes(nodes, params=input.params)
            references = await self.references_from_texts(texts)
        else:
            texts = []
            references = []
        context = KnwlContext(
            input=input,
            nodes=nodes,
            edges=edges,
            texts=texts,
            references=references,
        )
        return context

    async def augment_via_edges(self, input: KnwlInput) -> KnwlContext | None:
        """
        A strategy on its own, if you wish, to augment the input via edges and through this retrieve nodes, texts and references.
        """
        edges = await self.semantic_edge_search(input)
        if not edges:
            return KnwlContext.empty(input=input)
        nodes = await self.nodes_from_edges(edges)
        if input.params.return_chunks:
            texts = await self.text_from_edges(edges, query_param=input.params)
            references = await self.references_from_texts(texts)
        else:
            texts = []
            references = []
        context = KnwlContext(
            input=input,
            nodes=nodes,
            edges=edges,
            texts=texts,
            references=references,
        )
        return context
    
    @staticmethod
    def unique_chunk_ids(nodes: list[KnwlNode] | list[KnwlEdge]) -> list[str]:
        """
        Collects unique chunk Id's from a list of nodes or edges.
        """
        if nodes is None:
            raise ValueError("get_chunk_ids: parameter is None")
        if not len(nodes):
            return []
        lists = [n.chunk_ids for n in nodes if n.chunk_ids is not None]
        # flatten the list and remove duplicates
        return unique_strings(lists)

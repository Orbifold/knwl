from typing import Union

from knwl.di import defaults
from knwl.logging import log
from knwl.models import KnwlNode, KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.storage.graph_base import GraphStorageBase
from knwl.storage.vector_storage_base import VectorStorageBase
from knwl.summarization.summarization_base import SummarizationBase


@defaults("semantic_graph")
class SemanticGraph(SemanticGraphBase):

    def __init__(
        self,
        graph_store: GraphStorageBase = None,
        node_embeddings: VectorStorageBase = None,
        edge_embeddings: VectorStorageBase = None,
        summarization: SummarizationBase = None,
    ):
        super().__init__()
        self._graph_store: GraphStorageBase = graph_store
        self.node_embeddings: VectorStorageBase = node_embeddings
        self.edge_embeddings = edge_embeddings
        self.summarization = summarization
        if self._graph_store is None:
            raise ValueError("SemanticGraph: graph_store is required.")
        if not isinstance(self._graph_store, GraphStorageBase):
            raise ValueError("SemanticGraph: graph_store must be a GraphStorageBase instance.")
        if self.node_embeddings is None:
            raise ValueError("SemanticGraph: node_embeddings is required.")
        if not isinstance(self.node_embeddings, VectorStorageBase):
            raise ValueError(
                "SemanticGraph: node_embeddings must be a VectorStorageBase instance."
            )
        if self.edge_embeddings is None:
            raise ValueError("SemanticGraph: edge_embeddings is required.")
        if not isinstance(self.edge_embeddings, VectorStorageBase):
            raise ValueError(
                "SemanticGraph: edge_embeddings must be a VectorStorageBase instance."
            )
        if self.summarization is None:
            raise ValueError("SemanticGraph: summarization is required.")
        if not isinstance(self.summarization, SummarizationBase):
            raise ValueError(
                "SemanticGraph: summarization must be a SummarizationBase instance."
            )

    @property
    def graph(self) -> GraphStorageBase:
        return self._graph_store

    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None:
        # TODO: consider embedding of the description only
        # this uses the automatic embedding of the edge, via Chroma by default
        if edge is None:
            return

        try:
            if edge.id is None:
                log.error("Edge must have an ID to be embedded.")
                raise ValueError("Edge must have an Id to be embedded.")
            if edge.source_id is None or edge.target_id is None:
                log.error("Edge must have both source and target IDs to be embedded.")
                raise ValueError(
                    "Edge must have both source and target IDs to be embedded."
                )  # check endpoints exist
            if not await self.node_exists(edge.source_id):
                raise ValueError(
                    f"Source node {edge.source_id} does not exist in the graph."
                )
            if not await self.node_exists(edge.target_id):
                raise ValueError(
                    f"Target node {edge.target_id} does not exist in the graph."
                )
            # merge descriptions if edge already exists
            merge_edge = await self.merge_edge_descriptions(edge)
            # add to graph store
            await self._graph_store.upsert_edge(
                edge.source_id, edge.target_id, merge_edge
            )
            # add to embedding store
            await self.edge_embeddings.upsert(
                {edge.id: merge_edge.model_dump(mode="json")}
            )
            return merge_edge
        except Exception as e:
            log(e)
            raise e

    async def embed_edges(self, edges: list[KnwlEdge]) -> list[KnwlEdge]:
        if edges is None or len(edges) == 0:
            return []
        coll = []
        for e in edges:
            ne = await self.embed_edge(e)
            if ne is not None:
                coll.append(ne)
        return coll

    async def embed_node(self, node: KnwlNode) -> KnwlNode | None:
        if node is None:
            return None
        node = await self.merge_node_descriptions(node)
        # add to graph store
        await self._graph_store.upsert_node(node)
        # add to embedding store
        await self.node_embeddings.upsert({node.id: node.model_dump(mode="json")})
        return node

    async def merge_node_descriptions(self, node: KnwlNode) -> KnwlNode:
        """
        Merges the description of a given node with the existing description in the graph store, if
        the node already exists. The merging is done by summarizing both descriptions using the
        configured summarization service.

        This method does not upsert the node, only merges the descriptions if necessary.
        """
        # if the node exists, we summarize the existing description with the new one
        if await self.node_exists(node):
            existing_node = await self.get_node_by_id(node.id)
            if (
                existing_node is not None
                and existing_node.description is not None
                and node.description is not None
            ):
                # summarize the two descriptions
                summary = await self.summarization.summarize(
                    [existing_node.description, node.description]
                )
                if summary is not None and len(summary.strip()) > 0:
                    node.description = summary.strip()
        return node

    async def merge_edge_descriptions(self, edge: KnwlEdge) -> KnwlEdge:
        """
        Merges the description of a given edge with existing edges in the graph store that have the
        same source, target, and type. The merging is done by summarizing all descriptions using the
        configured summarization service.

        This method does not upsert the edge, only merges the descriptions if necessary.
        """
        # endpoints and type define the edge
        edges = await self.get_edges(edge.source_id, edge.target_id, edge.type)
        if edges and len(edges) > 0:
            edges.append(edge)
            # summarize the existing descriptions with the new one
            combined_description = await self.summarization.summarize(
                [e.description for e in edges if e.description]
            )
            if combined_description:
                # note that the id of the original edge is kept
                edge.description = combined_description.strip()
        return edge

    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]:
        if nodes is None or len(nodes) == 0:
            return []
        coll = []
        data = {}
        for node in nodes:
            if node is None:
                continue
            node = await self.merge_node_descriptions(node)
            data[node.id] = node.model_dump(mode="json")
            n = await self._graph_store.upsert_node(node)

            coll.append(n)

        # embedding of the nodes
        await self.node_embeddings.upsert(data)
        return [KnwlNode(**d) for d in coll]

    async def get_node_by_id(self, id: str) -> KnwlNode | None:
        if id is None or len(id.strip()) == 0:
            return None
        data = await self._graph_store.get_node_by_id(id)
        if data is None:
            return None
        if "data" in data and isinstance(data["data"], str):
            import json

            try:
                data["data"] = json.loads(data["data"])
            except Exception:
                pass
        self.fix_lists_in_data(data)

        return KnwlNode(**data)

    async def get_edge_by_id(self, id: str) -> KnwlEdge | None:
        if id is None or len(id.strip()) == 0:
            return None
        data = await self._graph_store.get_edge_by_id(id)
        if data is None:
            return None
        if "data" in data and isinstance(data["data"], str):
            import json

            try:
                data["data"] = json.loads(data["data"])
            except Exception:
                pass
        self.fix_lists_in_data(data)

        return KnwlEdge(**data)

    def fix_lists_in_data(self, data: dict):
        """
        Ensure that any list fields in the data dictionary are properly formatted as lists.
        This is particularly useful when data is stored in formats that may convert lists to strings.
        """
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                try:
                    import ast

                    data[key] = ast.literal_eval(value)
                except Exception:
                    pass
        return data

    async def node_exists(self, id: KnwlNode | str) -> bool:
        if isinstance(id, KnwlNode):
            id = id.id
        if id is None or len(id.strip()) == 0:
            return False
        return await self._graph_store.node_exists(id)

    async def edge_exists(self, id: KnwlEdge | str) -> bool:
        if isinstance(id, KnwlEdge):
            id = id.id
        if id is None or len(id.strip()) == 0:
            return False
        return await self._graph_store.edge_exists(id)

    async def get_edges(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ) -> Union[list[KnwlEdge], None]:
        found = await self._graph_store.get_edges(
            source_node_id_or_key, target_node_id, type
        )
        if found is None or len(found) == 0:
            return None
        edges = []
        for e in found:
            self.fix_lists_in_data(e)
            edges.append(KnwlEdge(**e))
        return edges

    async def merge_graph(self, graph):
        """
        Merge a graph into the semantic graph.

        Args:
            graph (KnwlGraph): The graph to merge.

        Returns:
            The merged graph.
        """
        if graph is None:
            return
        ns = await self.embed_nodes(graph.nodes)
        es = await self.embed_edges(graph.edges)
        g = KnwlGraph(nodes=ns, edges=es, keywords=graph.keywords, id=graph.id)
        return g

    async def consolidate_graphs(
        self, g1: KnwlGraph, g2: KnwlGraph
    ) -> KnwlGraph | None:
        """
        Consolidate two knowledge graphs into one, merging (descriptions of) nodes and edges.
        Does not store anything, just returns the consolidated graph.
        The returned graph has the id of g1.
        """
        if g1 is None and g2 is None:
            return None
        if g1 is None:
            return g2
        if g2 is None:
            return g1

        merged_nodes = {node.id: node for node in g1.nodes}
        for node in g2.nodes:
            if node.id in merged_nodes:
                # merge descriptions
                existing_node = merged_nodes[node.id]
                summary = await self.summarization.summarize(
                    [existing_node.description, node.description]
                )
                if summary is not None and len(summary.strip()) > 0:
                    merged_nodes[node.id].description = summary.strip()
            else:
                merged_nodes[node.id] = node

        merged_edges = {edge.id: edge for edge in g1.edges}
        for edge in g2.edges:
            if edge.id in merged_edges:
                # merge descriptions
                existing_edge = merged_edges[edge.id]
                summary = await self.summarization.summarize(
                    [existing_edge.description, edge.description]
                )
                if summary is not None and len(summary.strip()) > 0:
                    merged_edges[edge.id].description = summary.strip()
            else:
                merged_edges[edge.id] = edge

        return KnwlGraph(
            id=g1.id,
            nodes=list(merged_nodes.values()),
            edges=list(merged_edges.values()),
        )

    async def get_similar_nodes(self, node: KnwlNode, top_k: int = 5) -> list[KnwlNode]:
        """
        Retrieve nodes that are semantically similar to the given node.

        This method uses the node embeddings to find nodes that are most similar
        to the provided node based on their semantic content. The similarity is
        determined by querying the embedding space with the JSON representation
        of the input node.

        Args:
            node (KnwlNode): The reference node to find similar nodes for. Must have
                a valid id attribute.
            top_k (int, optional): The maximum number of similar nodes to return.
                Defaults to 5.

        Returns:
            list[KnwlNode]: A list of nodes that are most similar to the input node,
                ordered by similarity score (most similar first). Returns an empty
                list if the input node is None or has no id.
        """
        if node is None or node.id is None:
            return []
        results = await self.node_embeddings.nearest(
            node.model_dump_json(), top_k=top_k
        )
        nodes = []
        for r in results:
            nodes.append(KnwlNode(**r))
        return nodes

    async def get_similar_edges(self, edge: KnwlEdge, top_k: int = 5) -> list[KnwlEdge]:
        if edge is None or edge.id is None:
            return []
        results = await self.edge_embeddings.nearest(
            edge.model_dump_json(), top_k=top_k
        )
        # at this point you have to decide whether the graph or the vector db is considered for the actual data
        # if the vector db only contains embeddings, then you have to get the actual data from the graph store
        # for now we assume the vector db contains the actual data as well,
        edges = []
        for r in results:
            edges.append(KnwlEdge(**r))
        return edges

    async def node_count(self) -> int:
        return await self._graph_store.node_count()

    async def edge_count(self) -> int:
        return await self._graph_store.edge_count()

    async def clear(self) -> None:
        await self._graph_store.clear()
        await self.node_embeddings.clear()
        await self.edge_embeddings.clear()

    async def nearest_nodes(self, query, top_k=5):
        results = await self.node_embeddings.nearest(
            query, top_k=top_k, where={"type_name": "KnwlNode"}
        )
        nodes = []
        for r in results:
            # if same vector storage for nodes and edges, filter only nodes
            if r is not None and r["type_name"] == "KnwlNode":
                nodes.append(KnwlNode(**r))
        return nodes

    async def nearest_edges(self, query, top_k=5):
        results = await self.edge_embeddings.nearest(
            query, top_k=top_k, where={"type_name": "KnwlEdge"}
        )
        edges = []
        for r in results:
            if r is not None and r["type_name"] == "KnwlEdge":
                edges.append(KnwlEdge(**r))
        return edges

    async def get_attached_edges(self, nodes: list[KnwlNode]) -> list[KnwlEdge]:
        """
        Retrieve the edges attached to the given nodes.

        Args:
            nodes (list[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        if nodes is None:
            raise ValueError("get_attached_edges: parameter is None")
        if not len(nodes):
            return []
        found = await self._graph_store.get_attached_edges(nodes)
        coll = []
        for e in found:
            self.fix_lists_in_data(e)
            coll.append(KnwlEdge(**e))
        return coll
    async def get_edges_between_nodes(self, source_id: str, target_id: str) -> list[KnwlEdge]:
        """
        Retrieve edges between two nodes by their IDs from the knowledge graph.

        Args:
            source_id (str): The unique identifier of the source node.
            target_id (str): The unique identifier of the target node.
        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects representing the edges between the two nodes.
        """
        found = await self._graph_store.get_edges_between_nodes(source_id, target_id)
        coll = []
        for e in found:
            self.fix_lists_in_data(e)
            coll.append(KnwlEdge(**e))
        return coll

    async def get_nodes_by_name(self, name: str) -> list[KnwlNode] | None:
        if name is None or len(name.strip()) == 0:
            return None
        found = await self._graph_store.get_nodes_by_name(name)
        if found is None or len(found) == 0:
            return None
        nodes = []
        for n in found:
            self.fix_lists_in_data(n)
            nodes.append(KnwlNode(**n))
        return nodes

    async def node_degree(self, node_id: str) -> int:
        return await self.graph.node_degree(node_id)

    async def edge_degree(self, edge_or_source_id: str, target_id: str = None) -> int:
        return await self.graph.edge_degree(edge_or_source_id, target_id)

    async def assign_edge_degrees(self, edges: list[KnwlEdge]) -> list[int]:
        coll = []
        for e in edges:
            degree = await self.edge_degree(e.source_id, e.target_id)
            e.degree = degree
            coll.append(degree)
        return coll

    async def get_semantic_endpoints(
        self, edge_ids: list[str]
    ) -> dict[str, tuple[str, str]]:
        return await self.graph.get_semantic_endpoints(edge_ids)

    async def delete_node_by_id(self, node_id: str) -> bool:
        """
        Delete a node by its Id from the knowledge graph.
        Returns True if the node was deleted, False if it did not exist.
        """

        deleted = await self._graph_store.remove_node(node_id)
        if deleted:
            await self.node_embeddings.delete_by_id(node_id)
        return deleted

    def __repr__(self):
        return f"<SemanticGraph, graph={self._graph_store.__class__.__name__}, nodes={self.node_embeddings.__class__.__name__}, edge_embeddings={self.edge_embeddings.__class__.__name__}, summarization={self.summarization.__class__.__name__}>"

    def __str__(self):
        return self.__repr__()

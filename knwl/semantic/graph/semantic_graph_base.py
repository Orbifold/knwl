from abc import ABC, abstractmethod
from typing import Union

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlNode, KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph
from knwl.storage.graph_base import GraphStorageBase


class SemanticGraphBase(FrameworkBase, ABC):
    """
    Base class for semantic graph implementations.

    Graph store is just a storage backend for nodes and edges.
    A semantic graph also has
    - embeddings for nodes and edges
    - merges nodes/edges by combining multiple descriptions via LLMs
    - similarity search via embeddings

    You can do embeddings in various graph stores (e.g. Neo4j, TigerGraph, etc.) but the augmentation of description is something you do not have in those graph stores.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def graph(self) -> GraphStorageBase: ...

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear the entire semantic graph, removing all nodes and edges.
        """
        ...

    @abstractmethod
    async def embed_node(self, node: KnwlNode) -> KnwlNode | None:
        """
        Embed a knowledge node into the semantic graph.

        This method processes a KnwlNode and generates its semantic embedding,
        which can be used for similarity searches, clustering, and other
        semantic operations within the graph structure.

        Args:
            node (KnwlNode): The knowledge node to be embedded into the semantic graph.
                             Contains the content and metadata that will be processed
                             to generate the embedding representation.

        Returns:
            KnwlNode | None: The embedded node or None if the input is None.
        """
        ...

    @abstractmethod
    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]:
        """
        Embed multiple knowledge nodes into the semantic graph.

        Args:
            nodes (list[KnwlNode]): List of knowledge nodes to be embedded.

        Returns:
            list[KnwlNode]: List of embedded nodes.
        """
        ...

    @abstractmethod
    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None:
        """
        Embed a knowledge edge into the semantic graph.

        Args:
            edge (KnwlEdge): The knowledge edge to be embedded.

        Returns:
            KnwlEdge | None: The embedded edge or None if the input is None.
        """
        ...

    @abstractmethod
    async def embed_edges(self, edges: list[KnwlEdge]):
        """
        Embed multiple knowledge edges into the semantic graph.

        Args:
            edges (list[KnwlEdge]): List of knowledge edges to be embedded.

        Returns:
            List of embedded edges.
        """
        ...

    @abstractmethod
    async def merge_node_descriptions(self, node: KnwlNode) -> KnwlNode:
        """
        Merges the description of a given node with the existing description in the graph store, if
        the node already exists. The merging is done by summarizing both descriptions using the
        configured summarization service.

        This method does not upsert the node, only merges the descriptions if necessary.

        Args:
            node (KnwlNode): The node whose description should be merged.

        Returns:
            KnwlNode: The node with merged description.
        """
        ...

    @abstractmethod
    async def merge_edge_descriptions(self, edge: KnwlEdge) -> KnwlEdge:
        """
        Merges the description of a given edge with existing edges in the graph store that have the
        same source, target, and type. The merging is done by summarizing all descriptions using the
        configured summarization service.

        This method does not upsert the edge, only merges the descriptions if necessary.

        Args:
            edge (KnwlEdge): The edge whose description should be merged.

        Returns:
            KnwlEdge: The edge with merged description.
        """
        ...

    @abstractmethod
    async def get_node_by_id(self, id: str) -> KnwlNode | None:
        """
        Retrieve a node by its ID.

        Args:
            id (str): The ID of the node to retrieve.

        Returns:
            KnwlNode | None: The node if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_edge_by_id(self, id: str) -> KnwlEdge | None:
        """
        Retrieve an edge by its ID.

        Args:
            id (str): The ID of the edge to retrieve.

        Returns:
            KnwlEdge | None: The edge if found, None otherwise.
        """
        ...

    @abstractmethod
    async def node_exists(self, id: KnwlNode | str) -> bool:
        """
        Check if a node exists in the graph.

        Args:
            id (KnwlNode | str): The node or node ID to check.

        Returns:
            bool: True if the node exists, False otherwise.
        """
        ...

    @abstractmethod
    async def edge_exists(self, id: KnwlEdge | str) -> bool:
        """
        Check if an edge exists in the graph.

        Args:
            id (KnwlEdge | str): The edge or edge ID to check.

        Returns:
            bool: True if the edge exists, False otherwise.
        """
        ...

    @abstractmethod
    async def get_edges(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ) -> Union[list[KnwlEdge], None]:
        """
        Retrieve edges based on source node, optionally filtered by target node and type.

        Args:
            source_node_id_or_key (str): The source node ID or key.
            target_node_id (str, optional): The target node ID. Defaults to None.
            type (str, optional): The edge type. Defaults to None.

        Returns:
            Union[list[KnwlEdge], None]: List of edges if found, None otherwise.
        """
        ...

    @abstractmethod
    async def merge_graph(self, graph: KnwlGraph) -> KnwlGraph | None:
        """
        Merge a graph into the semantic graph.

        Args:
            graph (KnwlGraph): The graph to merge.

        Returns:
            The merged graph.
        """
        ...

    @abstractmethod
    async def get_similar_nodes(self, node: KnwlNode, top_k: int = 5) -> list[KnwlNode]:
        """
        Retrieve nodes that are semantically similar to the given node.

        This method uses the node embeddings to find nodes that are most similar
        to the provided node based on their semantic content.

        Args:
            node (KnwlNode): The reference node to find similar nodes for.
            top_k (int, optional): The maximum number of similar nodes to return.
                Defaults to 5.

        Returns:
            list[KnwlNode]: A list of nodes that are most similar to the input node,
                ordered by similarity score (most similar first).
        """
        ...

    @abstractmethod
    async def get_similar_edges(self, edge: KnwlEdge, top_k: int = 5) -> list[KnwlEdge]:
        """
        Retrieve edges that are semantically similar to the given edge.

        Args:
            edge (KnwlEdge): The reference edge to find similar edges for.
            top_k (int, optional): The maximum number of similar edges to return.
                Defaults to 5.

        Returns:
            list[KnwlEdge]: A list of edges that are most similar to the input edge,
                ordered by similarity score (most similar first).
        """
        ...

    @abstractmethod
    async def node_count(self) -> int:
        """
        Get the total number of nodes in the graph.

        Returns:
            int: The number of nodes.
        """
        ...

    @abstractmethod
    async def edge_count(self) -> int:
        """
        Get the total number of edges in the graph.

        Returns:
            int: The number of edges.
        """
        ...

    @abstractmethod
    async def consolidate_graphs(
        self, g1: KnwlGraph, g2: KnwlGraph
    ) -> KnwlGraph | None:
        """
        Consolidate two knowledge graphs into one, merging nodes and edges
        that are semantically similar.

        Args:
            g1 (KnwlGraph): The first knowledge graph.
            g2 (KnwlGraph): The second knowledge graph.

        Returns:
            KnwlGraph | None: The consolidated knowledge graph.
        """
        ...

    @abstractmethod
    async def nearest_nodes(self, query: str, top_k: int = 5) -> list[KnwlNode]:
        """
        Retrieve the nearest nodes to a given query string based on semantic similarity.

        Args:
            query (str): The query string to find nearest nodes for.
            top_k (int, optional): The maximum number of nearest nodes to return.
                Defaults to 5.

        Returns:
            list[KnwlNode]: A list of nodes that are nearest to the query,
                ordered by similarity score (most similar first).
        """
        ...

    @abstractmethod
    async def nearest_edges(self, query: str, top_k: int = 5) -> list[KnwlEdge]:
        """
        Retrieve the nearest edges to a given query string based on semantic similarity.

        Args:
            query (str): The query string to find nearest edges for.
            top_k (int, optional): The maximum number of nearest edges to return.
                Defaults to 5.

        Returns:
            list[KnwlEdge]: A list of edges that are nearest to the query,
                ordered by similarity score (most similar first).
        """
        ...

    @abstractmethod
    async def get_attached_edges(self, nodes: list[KnwlNode]) -> list[KnwlEdge]:
        """
        Retrieve the edges attached to the given nodes.

        Args:
            nodes (list[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        ...
    @abstractmethod
    async def get_edges_between_nodes(self, source_id: str, target_id: str) -> list[KnwlEdge]:
        """
        Retrieve edges between two nodes by their IDs from the knowledge graph.
        """
        ...

    @abstractmethod
    async def node_degree(self, node_id: str) -> int: ...

    @abstractmethod
    async def edge_degree(self, edge_or_source_id: str, target_id: str = None) -> int:
        """
        Retrieve the degree of an edge.
        Args:
            edge_or_source_id:
            target_id:

        Returns:

        """
        ...

    @abstractmethod
    async def assign_edge_degrees(self, edges: list[KnwlEdge]) -> list[int]: ...

    @abstractmethod
    async def get_semantic_endpoints(
        self, edge_ids: list[str]
    ) -> dict[str, tuple[str, str]]:
        """
        Returns the names of the source and target nodes for the given edge Id's.
        """
        ...

    @abstractmethod
    async def get_nodes_by_name(self, name: str) -> list[KnwlNode] | None:
        """
        The id of the node uniquely identifies it, but sometimes it's useful to get a node by its name.
        This means that this method may return multiple nodes with the same name.

        Args:
            name (str): The name of the node to retrieve.

        Returns:
            KnwlNode | None: The node if found, None otherwise.
        """
        ...

    @abstractmethod
    async def delete_node_by_id(self, node_id: str) -> bool:
        """
        Delete a node by its Id from the knowledge graph.
        Returns True if the node was deleted, False if it did not exist.
        """
        ...

from abc import ABC, abstractmethod
from typing import Union

from pydantic import BaseModel

from knwl.framework_base import FrameworkBase
from knwl.storage.storage_base import StorageBase


class GraphStorageBase(StorageBase, ABC):
    """
    Base class for graph storage implementations.
    Strictly speaking, the graph is a directed multigraph, meaning multiple edges can exist between the same pair of nodes.
    This abstract base class does not use the KnwlNode or KnwlEdge models directly, but the data is expected to be in the form of dictionaries
    that can be converted to/from those models. That is, you can use a GraphStorageBase independently of the higher level mechanisms in knwl.

    - The 'id' (string) should be unique for nodes and edges and present in the data (payload dictionary). If not provided, a uuid4 will be generated.
    - The 'name' (optional string) is not unique and can be the same for different nodes (e.g. "Apple" as fruit and as company).
    - The 'type' (string) is a semantic type (e.g. Person, Company, Location, Product, Event, etc.) and is optional. If not provided, it will be set to "Unknown".

    """

    @abstractmethod
    async def node_exists(self, node_id: str) -> bool:
        """
        Check if a node with the given Id exists in the graph.

        Args:
            node_id (str): The unique identifier of the node to check for existence.

        Returns:
            bool: True if the node exists in the graph, False otherwise.
        """
        ...

    @abstractmethod
    async def edge_exists(
        self,
        source_or_key: Union[BaseModel, str, dict],
        target_node_id: Union[BaseModel, str, dict] = None,
    ) -> bool:
        """
        Check if an edge exists between the given source and target nodes.

        Args:
            source_or_key ( Union[BaseModel,str,dict]): The unique identifier of the source node or edge.
            target_node_id ( Union[BaseModel,str,dict]): The unique identifier of the target node. If not provided, source_or_key is treated as the edge Id.

        Returns:
            bool: True if the edge exists, False otherwise.
        """
        ...

    @abstractmethod
    async def get_node_by_id(self, node_id: str) -> Union[dict, None]:
        """
        Retrieve a node from the graph by its unique identifier.

        Args:
            node_id (str): The unique identifier of the node to retrieve.

        Returns:
            Union[dict, None]: A dictionary containing the node data if found,
                              None if the node does not exist.
        """
        ...

    @abstractmethod
    async def get_nodes_by_name(self, node_name) -> Union[list[dict], None]:
        """
        Retrieves node(s) by its name.

        Args:
            node_name (str): The name of the node to retrieve.

        Returns:
            list[dict] | None: Since the name is not unique and can appear with different semantic types (e.g. Apple as fruit and as company), a list of dictionaries is returned if found, None otherwise.

        """
        ...

    @abstractmethod
    async def node_degree(self, node_id: str) -> int:
        """
        Retrieve the degree of a node in the graph.

        Args:
            node_id (str): The unique identifier of the node.

        Returns:
            int: The degree of the node, or 0 if the node does not exist.
        """
        ...

    @abstractmethod
    async def edge_degree(self, edge_or_source_id: str, target_id: str) -> int:
        """
        Retrieve the degree of an edge in the graph. The degree of an edge is defined as the number of connections it has to other edges (via its endpoints).

        Args:
            edge_or_source_id (str): The unique identifier of the source node.
            target_id (str): The unique identifier of the target node.

        Returns:
            int: The degree of the edge, or 0 if the edge does not exist.
        """
        ...

    @abstractmethod
    async def get_edges(
        self, source_node_id_or_key: str, target_node_id: str = None, label: str = None
    ) -> Union[list[dict], None]:
        """
        Retrieve edges from the graph based on the endpoints and optional label.

        Args:
            source_node_id_or_key (str): The unique id of the edge or the Id of the source node for the edge.
            target_node_id (str, optional): The ID of the target node for the edge.
                If None, returns all edges from the source node. Defaults to None.
            label (str, optional): The label/type of the edge to filter by.
                If None, returns edges regardless of label. Defaults to None.

        Returns:
            Union[list[dict], None]: A list of dictionaries representing the edge(s)
                if found, where each dictionary contains edge properties and metadata.
                Returns None if no edges are found matching the criteria.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by subclasses.
        """
        ...

    @abstractmethod
    async def get_node_edges(self, source_node_id: str) -> list[dict] | None:
        """
        Retrieves all edges connected to the given node.

        Args:
            source_node_id (str): The ID of the source node.

        Returns:
            list[dict] | None: A list of edge objects if the node exists, None otherwise.
        """
        ...

    @abstractmethod
    async def get_edges_between_nodes(
        self, source_id: str, target_id: str
    ) -> list[dict]:
        """
        Retrieve edges between two nodes by their IDs from the knowledge graph.
        """
        ...

    @abstractmethod
    async def get_attached_edges(self, nodes):
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (list[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        ...

    @abstractmethod
    async def get_edge_degrees(self, edges):
        """
        Asynchronously retrieves the degrees of the given edges.

        Args:
            edges (list[KnwlEdge]): A list of KnwlEdge objects for which to retrieve degrees.

        Returns:
            list[int]: A list of degrees for the given edges.
        """
        ...

    @abstractmethod
    async def get_semantic_endpoints(
        self, edge_ids: list[str]
    ) -> dict[str, tuple[str, str]]:
        """
        Given a list of edge Id's, the name of the source and target nodes is returned as tuple (source_name, target_name).
        The keys of the returned dictionary are the edge Id's.

        example return value:
        `
        {
            "edge_id_1": ("source_node_name_1", "target_node_name_1"),
            "edge_id_2": ("source_node_name_2", "target_node_name_2"),
            ...
        }
        `

        Args:
            edge_ids (list[str]): A list of node IDs for which to retrieve names.
        """
        ...

    @abstractmethod
    async def get_edge_by_id(self, edge_id: str) -> Union[dict, None]:
        """
        Retrieve an edge from the graph by its unique identifier.

        Args:
            edge_id (str): The unique identifier of the edge to retrieve.

        Returns:
            Union[dict, None]: A dictionary containing the edge data if found,
                              None if the edge does not exist.
        """
        ...

    @abstractmethod
    async def upsert_node(self, node_id: BaseModel | str | dict, node_data=None):
        """
        Insert or update a node in the graph storage.

        This method creates a new node if it doesn't exist, or updates an existing node
        with the provided data. The operation is performed asynchronously.

        Args:
            node_id (BaseModel|str|dict): Unique identifier for the node to upsert or a dictionary containing node properties.
            node_data (optional): Data to associate with the node. Can be any type
                depending on the storage implementation. Defaults to None.

        Returns:
            None: This method performs the upsert operation but doesn't return a value.
        """
        ...

    @abstractmethod
    async def upsert_edge(self, source_node_id, target_node_id, edge_data=None):
        """
        Upsert (insert or update) an edge in the graph.

        Args:
            source_node_id: The identifier of the source node for the edge
            target_node_id: The identifier of the target node for the edge
            edge_id (str, optional): Unique identifier for the edge. If None, may be auto-generated
            edge_data (optional): Additional data/properties to associate with the edge

        Returns:
            The result of the upsert operation (implementation-specific)
        """
        ...

    @abstractmethod
    async def clear(self):
        """
        Clear all data from the graph storage.

        This method removes all nodes, edges, and associated data from the graph storage,
        effectively resetting it to an empty state.

        Returns:
            None
        """
        ...

    @abstractmethod
    async def node_count(self):
        """
        Get the total number of nodes in the graph.

        Returns:
            int: The total count of nodes in the graph storage.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        ...

    @abstractmethod
    async def edge_count(self):
        """
        Get the total number of edges in the graph.

        Returns:
            int: The total count of edges in the graph storage.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        ...

    @abstractmethod
    async def remove_node(self, node_id: str):
        """
        Remove a node from the graph storage.

        Args:
            node_id (str): The unique identifier of the node to be removed.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
            ValueError: If the node_id is invalid or empty.
            KeyError: If the node with the given node_id does not exist.

        Note:
            This method should also handle cleanup of any edges connected to the node
            being removed to maintain graph integrity.
        """
        ...

    @abstractmethod
    async def remove_edge(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ):
        """Remove an edge from the graph.

        Args:
            source_node_id_or_key (str): The ID or key of the source node, or an edge key
                                        if target_node_id is None.
            target_node_id (str, optional): The ID of the target node. If None,
                                           source_node_id_or_key is treated as an edge key.

        Raises:
            KeyError: If the specified edge does not exist in the graph.
            ValueError: If the provided node IDs are invalid.

        Returns:
            None

        Note:
            This method removes the edge from the graph storage. If 'source_node_id_or_key'
            is provided alone, it should be a unique edge identifier. If both parameters
            are provided, they represent the source and target nodes of the edge to remove.
        """
        ...

    @abstractmethod
    async def get_edge_weights(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ) -> dict[str, float]:
        """
        Get the weights of edges between two nodes in the graph.

        Args:
            source_node_id_or_key (str): The ID or key of the source node.
            target_node_id (str, optional): The ID of the target node. If None,
                the source_node_id_or_key is treated as an edge key. Defaults to None.
            type (str, optional): The type of the edge weight. Defaults to None.
        Returns:
            dict[str, float]: A dictionary where keys are edge types and values are their corresponding weights.
                If no edges are found, an empty dictionary is returned.
        """
        ...

    @abstractmethod
    async def merge(self, nodes: list[dict], edges: list[dict]) -> None:
        """
        Merge another graph into the current graph storage.

        Args:
            nodes (list[dict]): A list of node dictionaries to merge into the graph.
            edges (list[dict]): A list of edge dictionaries to merge into the graph.

        Returns:
            None

        Note:
            This method should handle merging nodes and edges from the provided graph
            into the existing graph storage, ensuring no duplicates and maintaining integrity.
        """
        ...


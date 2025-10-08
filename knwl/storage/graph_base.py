from abc import abstractmethod
from typing import Union

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlEdge
from knwl.models import KnwlNode


class GraphBase(FrameworkBase):

    @abstractmethod
    def node_exists(self, node_id):
        pass

    @abstractmethod
    def edge_exists(self, source_or_key, target_node_id):
        pass

    @abstractmethod
    def get_node_by_id(self, node_id) -> Union[KnwlNode, None]:
        pass

    @abstractmethod
    def get_node_by_name(self, node_name) -> Union[list[KnwlNode], None]:
        """
        Retrieves a node(s) by its name.
        Args:
            node_name: The name of the node to retrieve.

        Returns:
            List[KnwlNode] | None: Since the name is not unique and can appear with different semantic types (e.g. Apple as fruit and as company), a list of KnwlNode objects is returned if found, None otherwise.

        """
        pass

    @abstractmethod
    def node_degree(self, node_id):
        pass

    @abstractmethod
    def edge_degree(self, source_id, target_id):
        pass

    @abstractmethod
    async def get_edge(self, source_node_id, target_node_id, label:str) -> Union[list[KnwlEdge], None]:
        pass

    @abstractmethod
    def get_node_edges(self, source_node_id):
        """
        Retrieves all edges connected to the given node.

        Args:
            source_node_id (str): The ID of the source node.

        Returns:
            List[KnwlEdge] | None: A list of KnwlEdge objects if the node exists, None otherwise.
        """
        pass

    @abstractmethod
    def get_attached_edges(self, nodes):
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (List[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            List[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        pass

    @abstractmethod
    def get_edge_degrees(self, edges):
        """
        Asynchronously retrieves the degrees of the given edges.

        Args:
            edges (List[KnwlEdge]): A list of KnwlEdge objects for which to retrieve degrees.

        Returns:
            List[int]: A list of degrees for the given edges.
        """
        pass

    @abstractmethod
    def get_semantic_endpoints(self, edge_ids):
        """
        Asynchronously retrieves the names of the nodes with the given IDs.

        Args:
            edge_ids (List[str]): A list of node IDs for which to retrieve names.

        Returns:
            List[str]: A list of node names.
        """
        pass

    @abstractmethod
    def get_edge_by_id(self, edge_id):
        pass

    @abstractmethod
    def upsert_node(self, node_id, node_data):
        pass

    @abstractmethod
    def upsert_edge(self, source_node_id, target_node_id, edge_data):
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def node_count(self):
        pass

    @abstractmethod
    def edge_count(self):
        pass

    @abstractmethod
    def remove_node(self, node_id):
        pass

    @abstractmethod
    def remove_edge(self, source_node_id, target_node_id):
        pass

    @abstractmethod
    def get_nodes(self):
        pass

    @abstractmethod
    def get_edges(self):
        pass

    @abstractmethod
    def get_edge_weight(self, source_node_id, target_node_id):
        pass


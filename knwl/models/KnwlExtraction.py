from dataclasses import dataclass, field
from typing import List
from uuid import uuid4

from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.utils import get_endpoint_ids


@dataclass(frozen=False)
class KnwlExtraction:
    """
    A class used to represent a Knowledge Extraction.
    Note that the id's of the nodes and edges are semantic, ie. actual names.
    The conversion to real identifiers happens downstream when this is merged into the knowledge graph.

    Attributes
    ----------
    nodes : dict[str, List[KnwlNode]]
        A dictionary where the keys are strings and the values are lists of KnwlNode objects.
    edges : dict[str, List[KnwlEdge]]
        A dictionary where the keys are strings and the values are lists of KnwlEdge objects.
        Note that the key is the tuple of endpoints sorted in ascending order.
        The KG is undirected and the key is used to ensure that the same edge is not added twice.
    typeName : str
        A string representing the type name of the extraction, default is "KnwlExtraction".
    id : str
        A unique identifier for the extraction, default is a new UUID4 string.
    """
    nodes: dict[str, List[KnwlNode]]
    edges: dict[str, List[KnwlEdge]]
    typeName: str = "KnwlExtraction"
    id: str = field(default=str(uuid4()))

    def is_consistent(self) -> bool:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_ids = self.get_node_ids()
        edge_ids = self.get_edge_ids()

        for edge in self.edges:
            source_id, target_id = get_endpoint_ids(edge)
            if source_id is None or target_id is None:
                return False
            if source_id not in node_ids or target_id not in node_ids:
                return False
        return True

    def make_consistent(self):
        """
        Make the graph consistent: remove edges with endpoints that are not in the node list.
        """
        node_ids = self.get_node_ids()
        edge_ids = self.get_edge_ids()
        new_edges = {}
        for edge in self.edges:
            source_id, target_id = get_endpoint_ids(edge)
            if source_id is not None and target_id is not None:
                if source_id in node_ids and target_id in node_ids:
                    new_edges[edge] = self.edges[edge]
        self.edges = new_edges

    def get_node_ids(self) -> List[str]:
        return self.nodes.keys()

    def get_edge_ids(self) -> List[str]:
        return self.edges.keys()

    def __post_init__(self):
        if not self.is_consistent():
            print("Warning: the extracted graph is not consistent, fixing this.")
            self.make_consistent()

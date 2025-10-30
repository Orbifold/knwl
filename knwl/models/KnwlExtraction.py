from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.utils import get_endpoint_ids
from knwl.logging import log


class KnwlExtraction(BaseModel):
    """
    A class used to represent a Knowledge Extraction.
    Note that the id's of the nodes and edges are semantic, ie. actual names.
    The conversion to real identifiers happens downstream when this is merged into the knowledge graph.

    Attributes
    ----------
    nodes : dict[str, list[KnwlNode]]
        A dictionary where the keys are names of entities and the values are lists of KnwlNode objects. These can have different types and descriptions.
    edges : dict[str, list[KnwlEdge]]
        A dictionary where the keys are strings and the values are lists of KnwlEdge objects.
        Note that the key is the tuple of endpoints sorted in ascending order.
        The KG is undirected and the key is used to ensure that the same edge is not added twice.
    typeName : str
        A string representing the type name of the extraction, default is "KnwlExtraction".
    id : str
        A unique identifier for the extraction, default is a new UUID4 string.

    """

    nodes: dict[str, list[KnwlNode]]
    edges: dict[str, list[KnwlEdge]]
    keywords: list[str] = Field(default_factory=list)
    typeName: str = "KnwlExtraction"
    id: str = Field(default_factory=lambda: str(uuid4()))

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate that the graph is consistent after initialization."""
        if not self.is_consistent():
            log.debug("Warning: the extracted graph is not consistent, fixing this.")
            self.make_consistent()
        return self

    def is_consistent(self) -> bool:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_keys = self.get_node_keys()
        edge_keys = self.get_edge_keys()

        for edge in self.edges:
            source_id, target_id = get_endpoint_ids(edge)
            if source_id is None or target_id is None:
                return False
            if source_id not in node_keys or target_id not in node_keys:
                return False
        return True

    def make_consistent(self):
        """
        Make the graph consistent: remove edges with endpoints that are not in the node list.
        """
        node_keys = self.get_node_keys()
        edge_keys = self.get_edge_keys()
        new_edges = {}
        for edge in self.edges:
            source_id, target_id = get_endpoint_ids(edge)
            if source_id is not None and target_id is not None:
                if source_id in node_keys and target_id in node_keys:
                    new_edges[edge] = self.edges[edge]
        self.edges = new_edges

    def get_node_ids(self) -> list[str]:
        coll = []
        for k in self.nodes.keys():
            for n in self.nodes[k]:
                coll.append(n.id)
        return coll

    def get_edge_ids(self) -> list[str]:
        coll = []
        for k in self.edges.keys():
            for e in self.edges[k]:
                coll.append(e.id)
        return coll

    def get_node_keys(self) -> list[str]:
        return list(self.nodes.keys())

    def get_edge_keys(self) -> list[str]:
        return list(self.edges.keys())

    def get_all_node_types(self) -> list[str]:
        types = set()
        for k in self.nodes.keys():
            for n in self.nodes[k]:
                types.add(n.type)
        return list(types)

    def get_all_edge_types(self) -> list[str]:
        types = set()
        for k in self.edges.keys():
            for e in self.edges[k]:
                for t in e.keywords:
                    types.add(t)
        return list(types)

    def get_name_by_type(self, entity_type: str) -> list[str]:
        """Get all nodes of a specific type."""
        coll = set()
        for k in self.nodes.keys():
            for n in self.nodes[k]:
                if n.type == entity_type:
                    coll.add(n.name)
        return list(coll)

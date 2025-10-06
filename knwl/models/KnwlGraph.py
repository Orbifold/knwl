from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode


class KnwlGraph(BaseModel):
    """
    A class used to represent a Knowledge Graph.
    This class is almost identical to KnwlExtraction, but the KnwlExtraction can have an entity name mapping to multiple nodes (eg. "Apple" can be a company or a fruit).
    In contrast, KnwlGraph has a flat list of nodes and edges.

    Attributes
    ----------
    nodes : List[KnwlNode]
        A list of KnwlNode objects.
    edges : List[KnwlEdge]
        A list of KnwlEdge objects.
    typeName : str
        A string representing the type name of the graph, default is "KnwlGraph".
    id : str
        A unique identifier for the graph, default is a new UUID4 string.
    """
    nodes: List[KnwlNode]
    edges: List[KnwlEdge]
    typeName: str = "KnwlGraph"
    id: str = Field(default_factory=lambda: str(uuid4()))

    model_config = {"frozen": True}

    def is_consistent(self) -> bool:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_ids = self.get_node_ids()
        edge_ids = self.get_edge_ids()

        for edge in self.edges:
            if edge.sourceId not in node_ids or edge.targetId not in node_ids:
                return False
        return True

    def get_node_ids(self) -> List[str]:
        return [node.id for node in self.nodes]

    def get_edge_ids(self) -> List[str]:
        return [edge.id for edge in self.edges]

    @model_validator(mode='after')
    def validate_consistency(self):
        """Validate that the graph is consistent after initialization."""
        if not self.is_consistent():
            raise ValueError("The graph is not consistent.")
        return self

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

    """

    nodes: List[KnwlNode]
    edges: List[KnwlEdge]
    keywords: List[str] = Field(default_factory=list)
    type_name: str = Field(
        default="KnwlGraph",
        frozen=True,
        description="The type name of the graph for (de)serialization purposes.",
    )
    id: str = Field(default=None, description="The unique identifier of the graph.")

    model_config = {"frozen": True}

    def is_consistent(self) -> str | None:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_ids = self.get_node_ids()

        for edge in self.edges:
            if edge.source_id not in node_ids:
                return f"Inconsistent graph: source endpoint '{edge.source_id}' does not exist in the graph."

            if edge.target_id not in node_ids:
                return f"Inconsistent graph: target endpoint '{edge.target_id}' does not exist in the graph."

        return None

    def get_node_ids(self) -> List[str]:
        return [node.id for node in self.nodes]

    def get_edge_ids(self) -> List[str]:
        return [edge.id for edge in self.edges]

    def get_node_names(self) -> List[str]:
        return [node.name for node in self.nodes]

    def get_node_types(self) -> List[str]:
        return [node.type for node in self.nodes]
    
    def get_node_descriptions(self) -> List[str]:
        return [node.description for node in self.nodes]

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate that the graph is consistent after initialization."""
        msg = self.is_consistent()
        if msg is not None:
            raise ValueError(msg)
        if self.id is None:
            object.__setattr__(self, "id", str(uuid4()))
        return self

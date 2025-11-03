from typing import Dict, List
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

    nodes: list[KnwlNode]
    edges: list[KnwlEdge]
    keywords: list[str] = Field(default_factory=list)
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

    def get_node_ids(self) -> list[str]:
        return [node.id for node in self.nodes]

    def get_edge_ids(self) -> list[str]:
        return [edge.id for edge in self.edges]

    def get_node_names(self) -> list[str]:
        return [node.name for node in self.nodes]

    def get_node_types(self) -> list[str]:
        return [node.type for node in self.nodes]

    def get_node_descriptions(self) -> list[str]:
        return [node.description for node in self.nodes]

    def get_node_by_id(self, id: str) -> KnwlNode | None:
        for node in self.nodes:
            if node.id == id:
                return node
        return None

    def get_edge_by_id(self, id: str) -> KnwlEdge | None:
        for edge in self.edges:
            if edge.id == id:
                return edge
        return None

    def is_empty(self) -> bool:
        return len(self.nodes) == 0 and len(self.edges) == 0

    def node_exists(self, id: KnwlNode | str) -> bool:
        node_id = id.id if isinstance(id, KnwlNode) else id
        return node_id in self.get_node_ids()

    def edge_exists(self, id: KnwlEdge | str) -> bool:
        edge_id = id.id if isinstance(id, KnwlEdge) else id
        return edge_id in self.get_edge_ids()

    def merge(self, other: "KnwlGraph") -> "KnwlGraph":
        """
        Merge another KnwlGraph into this one and return a new KnwlGraph.
        The id of the merged graph is the same as this graph.
        Note: this is not semantically aware merging, it simply concatenates the nodes and edges.
        """
        # unique nodes by id
        merged_nodes_dict: Dict[str, KnwlNode] = {}
        for node in self.nodes + other.nodes:
            merged_nodes_dict[node.id] = node
        merged_nodes = list(merged_nodes_dict.values())

        # unique edges by id
        merged_edges_dict: Dict[str, KnwlEdge] = {}
        for edge in self.edges + other.edges:
            merged_edges_dict[edge.id] = edge
        merged_edges = list(merged_edges_dict.values())

        return KnwlGraph(
            id=self.id,
            nodes=merged_nodes,
            edges=merged_edges,
            keywords=list(set(self.keywords + other.keywords)),
        )

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate that the graph is consistent after initialization."""
        msg = self.is_consistent()
        if msg is not None:
            raise ValueError(msg)
        if self.id is None:
            object.__setattr__(self, "id", str(uuid4()))
        return self

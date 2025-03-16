from knwl.utils import hash_with_prefix


from dataclasses import dataclass, field
from typing import List
from uuid import uuid4


@dataclass(frozen=True)
class KnwlEdge:
    """
    Represents a knowledge edge in a graph.

    Attributes:
        sourceId (str): The ID of the source node.
        targetId (str): The ID of the target node.
        chunkIds (str): The ID of the chunk.
        weight (float): The weight of the edge.
        description (str): A description of the edge.
        keywords (List(str)): Keywords associated with the edge.
        typeName (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
    """
    sourceId: str
    targetId: str
    typeName: str = "KnwlEdge"
    id: str = field(default=str(uuid4()))
    chunkIds: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    description: str = field(default=None)
    weight: float = field(default=1.0)

    @staticmethod
    def hash_edge(e: 'KnwlEdge') -> str:
        return hash_with_prefix(e.sourceId + " " + e.targetId + " " + (e.description or "") + str(e.weight), prefix="edge-")

    def update_id(self):
        #  note that using only source and target is not enough to ensure uniqueness
        object.__setattr__(self, "id", KnwlEdge.hash_edge(self))

    def __post_init__(self):
        if self.sourceId is None or len(str.strip(self.sourceId)) == 0:
            raise ValueError("Source Id of a KnwlEdge cannot be None or empty.")
        if self.targetId is None or len(str.strip(self.targetId)) == 0:
            raise ValueError("Target Id of a KnwlEdge cannot be None or empty.")
        self.update_id()

    @staticmethod
    def other_endpoint(edge: 'KnwlEdge', node_id: str) -> str:
        if edge.sourceId == node_id:
            return edge.targetId
        elif edge.targetId == node_id:
            return edge.sourceId
        else:
            raise ValueError(f"Node {node_id} is not an endpoint of edge {edge.id}")
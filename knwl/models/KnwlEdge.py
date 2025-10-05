from knwl.utils import hash_with_prefix

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from uuid import uuid4


class KnwlEdge(BaseModel):
    """
    Represents a knowledge edge in a graph.

    Attributes:
        sourceId (str): The ID of the source node.
        targetId (str): The ID of the target node.
        chunkIds (List[str]): The IDs of the chunks.
        weight (float): The weight of the edge.
        description (Optional[str]): A description of the edge.
        keywords (List[str]): Keywords associated with the edge.
        typeName (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
    """
    
    model_config = {"frozen": True}
    
    sourceId: str
    targetId: str
    typeName: str = "KnwlEdge"
    id: str = Field(default_factory=lambda: str(uuid4()))
    chunkIds: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    weight: float = 1.0

    @staticmethod
    def hash_edge(e: 'KnwlEdge') -> str:
        return hash_with_prefix(e.sourceId + " " + e.targetId + " " + (e.description or "") + str(e.weight), prefix="edge-")

    @field_validator('sourceId')
    @classmethod
    def validate_source_id(cls, v):
        if v is None or len(str(v).strip()) == 0:
            raise ValueError("Source Id of a KnwlEdge cannot be None or empty.")
        return v

    @field_validator('targetId')
    @classmethod
    def validate_target_id(cls, v):
        if v is None or len(str(v).strip()) == 0:
            raise ValueError("Target Id of a KnwlEdge cannot be None or empty.")
        return v

    @model_validator(mode='after')
    def update_id(self):
        # Note that using only source and target is not enough to ensure uniqueness
        object.__setattr__(self, "id", KnwlEdge.hash_edge(self))
        return self

    @staticmethod
    def other_endpoint(edge: 'KnwlEdge', node_id: str) -> str:
        if edge.sourceId == node_id:
            return edge.targetId
        elif edge.targetId == node_id:
            return edge.sourceId
        else:
            raise ValueError(f"Node {node_id} is not an endpoint of edge {edge.id}")
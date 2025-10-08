from knwl.utils import hash_with_prefix

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from uuid import uuid4


class KnwlEdge(BaseModel):
    """
    Represents a knowledge edge in a graph.

    Attributes:
        source_id (str): The ID of the source node.
        target_id (str): The ID of the target node.
        chunk_ids (List[str]): The IDs of the chunks.
        weight (float): The weight of the edge.
        description (Optional[str]): A description of the edge.
        keywords (List[str]): Keywords associated with the edge.
        type_name (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
    """

    model_config = {"frozen": True}

    source_id: str = Field( description="The Id of the source node.")
    target_id: str = Field( description="The Id of the target node.")
    type_name: str = Field(
        default="KnwlEdge",
        frozen=True,
        description="The type name of the edge for (de)serialization purposes.",
    )
    id: str = Field(default_factory=lambda: str(uuid4()))
    chunk_ids: Optional[list[str]] = Field(default_factory=list)
    keywords: Optional[list[str]] = Field(
        default_factory=list,
        description="Keywords associated with the edge. These can be used as types or labels in a property graph. Note that the names of the keywords should ideally be from an ontology.",
    )
    description: Optional[str] = Field(
        default=None, description="A description of the edge."
    )
    weight: float = Field(
        default=1.0,
        description="The weight of the edge. This can be used to represent the strength or importance of the relationship. This is given by domain experts or derived from data extraction.",
    )

    @staticmethod
    def hash_edge(e: "KnwlEdge") -> str:
        return hash_with_prefix(
            e.source_id
            + " "
            + e.target_id
            + " "
            + (e.description or "")
            + str(e.weight),
            prefix="edge-",
        )

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, v):
        if v is None or len(str(v).strip()) == 0:
            raise ValueError("Source Id of a KnwlEdge cannot be None or empty.")
        return v

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, v):
        if v is None or len(str(v).strip()) == 0:
            raise ValueError("Target Id of a KnwlEdge cannot be None or empty.")
        return v

    @model_validator(mode="after")
    def update_id(self):
        # Note that using only source and target is not enough to ensure uniqueness
        object.__setattr__(self, "id", KnwlEdge.hash_edge(self))
        return self

    @staticmethod
    def other_endpoint(edge: "KnwlEdge", node_id: str) -> str:
        if edge.source_id == node_id:
            return edge.targetId
        elif edge.targetId == node_id:
            return edge.source_id
        else:
            raise ValueError(f"Node {node_id} is not an endpoint of edge {edge.id}")

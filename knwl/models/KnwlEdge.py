from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlEdge(BaseModel):
    """
    Represents a relation between atoms of knowledge.

    Minimum required fields are source_id, target_id and type.
    Contrary to most models this one is not immutable because it complicates the grag algorithms too much.

    Attributes:
        source_id (str): The Id of the source node.
        target_id (str): The Id of the target node.
        chunk_ids (list[str]): The IDs of the chunks.
        weight (float): The weight of the edge.
        description (Optional[str]): A description of the edge.
        keywords (list[str]): Keywords associated with the edge.
        type_name (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
    """

    degree: Optional[int] = Field(
        default=None, description="The degree of the edge in the graph."
    )
    source_id: str = Field(description="The Id of the source node.")
    target_id: str = Field(description="The Id of the target node.")
    source_name: Optional[str] = Field(
        default=None, description="The name of the source node."
    )
    target_name: Optional[str] = Field(
        default=None, description="The name of the target node."
    )
    type: Optional[str] = Field(
        default="Unknown",
        description="The type of the relation. In a property modeled graph this should be an ontology class.",
    )
    type_name: str = Field(
        default="KnwlEdge",
        frozen=True,
        description="The type name of the edge for (de)serialization purposes.",
    )
    id: Optional[str] = Field(
        default=None,
        description="The unique identifier of the node, automatically generated from the required fields.",
    )
    chunk_ids: Optional[list[str]] = Field(
        default_factory=list,
        description="The chunk identifiers associated with this edge.",
    )
    keywords: Optional[list[str]] = Field(
        default_factory=list,
        description="Keywords associated with the edge. These can be used as types or labels in a property graph. Note that the names of the keywords should ideally be from an ontology.",
    )

    description: Optional[str] = Field(
        default="", description="A description of the edge."
    )
    weight: Optional[float] = Field(
        default=1.0,
        description="The weight of the edge. This can be used to represent the strength or importance of the relationship. This is given by domain experts or derived from data extraction.",
    )
    index: Optional[int] = Field(
        default=0, description="The index of the edge within the parent list, if any."
    )
    data: Optional[dict] = Field(
        default_factory=dict,
        description="Additional data associated with the knowledge node.",
    )

    @staticmethod
    def hash_edge(e: "KnwlEdge") -> str:
        return hash_with_prefix(
            e.source_id + " " + e.target_id + " " + e.type,
            prefix="edge|>",
        )

    def has_data(self, key: str) -> bool:
        """
        Check if the KnwlNode has any additional data.

        Returns:
            bool: True if the data dictionary is not empty, False otherwise.
        """

        return key in self.data

    def get_data(self, key: str):
        """
        Get additional data associated with the KnwlNode.

        Returns:
            The value associated with the key in the data dictionary, or None if the key does not exist.
        """

        return self.data.get(key, None)

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

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v is None or len(str(v).strip()) == 0:
            raise ValueError("Type of a KnwlEdge cannot be None or empty.")
        return v.strip().replace("<", "").replace(">", "") # sanitize accidents from LLMs

    @model_validator(mode="after")
    def update_id(self):
        # Note that using only source and target is not enough to ensure uniqueness
        if self.id is None:
            object.__setattr__(self, "id", KnwlEdge.hash_edge(self))
        if self.type is None or len(self.type.strip()) == 0:
            if self.keywords and len(self.keywords) > 0:
                object.__setattr__(self, "type", self.keywords[0])
            else:
                object.__setattr__(self, "type", "Unknown")
        return self

    @field_validator("data", mode="before")
    @classmethod
    def parse_data(cls, v):
        """Parse JSON string to dict if needed."""
        if v is not None and isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string for data field: {e}")
        return v

    @staticmethod
    def other_endpoint(edge: "KnwlEdge", node_id: str) -> str:
        if edge.source_id == node_id:
            return edge.target_id
        elif edge.target_id == node_id:
            return edge.source_id
        else:
            raise ValueError(f"Node {node_id} is not an endpoint of edge {edge.id}")

    def to_text(self) -> str:
        return f"""
Type: {self.type}
Source: {self.source_name}
Target: {self.target_name}
Description: {self.description}
Keywords: {', '.join(self.keywords) if self.keywords else 'None'}
    """
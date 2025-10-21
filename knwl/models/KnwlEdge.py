from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlEdge(BaseModel):
    """
    Represents a relation between atoms of knowledge.

    Minimum required fields are source_id, target_id and type.
    This is an immutable class, use the update() method to create a new instance with updated fields.

    Attributes:
        source_id (str): The Id of the source node.
        target_id (str): The Id of the target node.
        chunk_ids (List[str]): The IDs of the chunks.
        weight (float): The weight of the edge.
        description (Optional[str]): A description of the edge.
        keywords (List[str]): Keywords associated with the edge.
        type_name (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
    """

    model_config = {"frozen": True}

    source_id: str = Field(description="The Id of the source node.")
    target_id: str = Field(description="The Id of the target node.")
    type: str = Field(
        default="Unknown",
        description="The type of the relation. In a property modeled graph this should be an ontology class.",
    )
    type_name: str = Field(
        default="KnwlEdge",
        frozen=True,
        description="The type name of the edge for (de)serialization purposes.",
    )
    id: str = Field(
        default=None,
        description="The unique identifier of the node, automatically generated from the required fields.",
        init=False,
    )
    chunk_ids: List[str] = Field(
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
    weight: float = Field(
        default=1.0,
        description="The weight of the edge. This can be used to represent the strength or importance of the relationship. This is given by domain experts or derived from data extraction.",
    )
    data: dict = Field(
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
        return v

    @model_validator(mode="after")
    def update_id(self):
        # Note that using only source and target is not enough to ensure uniqueness
        object.__setattr__(self, "id", KnwlEdge.hash_edge(self))
        if self.type is None or len(self.type.strip()) == 0:
            if self.keywords and len(self.keywords) > 0:
                object.__setattr__(self, "type", self.keywords[0])
            else:
                object.__setattr__(self, "type", "Unknown")
        return self

    @staticmethod
    def other_endpoint(edge: "KnwlEdge", node_id: str) -> str:
        if edge.source_id == node_id:
            return edge.target_id
        elif edge.target_id == node_id:
            return edge.source_id
        else:
            raise ValueError(f"Node {node_id} is not an endpoint of edge {edge.id}")

    def update(self, **kwargs) -> "KnwlEdge":
        """
        Create a new KnwlNode instance with updated fields. Only 'type', 'description', 'weight', 'keywords', 'chunk_ids', and 'data' are allowed.
        """
        allowed_fields = {"type", "description", "weight", "keywords", "chunk_ids", "data"}
        invalid_fields = set(kwargs.keys()) - allowed_fields
        if invalid_fields:
            raise ValueError(
                f"Invalid fields: {invalid_fields}. Only 'type', 'description', 'weight', 'keywords', 'chunk_ids', and 'data' are allowed."
            )
        new_edge = self.model_copy(update=kwargs)
        # pydantic does not call the model_validator on model_copy, so we need to set the id manually
        object.__setattr__(new_edge, "id", self.hash_edge(new_edge))
        return new_edge

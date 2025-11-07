from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlNode(BaseModel):
    """
    An atom of knowledge.

    Minimum required fields are name and type, the id is a hash of these two fields.
    Contrary to most models this one is not immutable because it complicates the grag algorithms too much.

    Attributes:
        name (str): The name of the knowledge node. Can be unique but in a refined model it should not. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.
        type (str): The type of the knowledge node.
        degree (int): The degree of the knowledge node in the graph.
        description (str): A description of the knowledge node.
        chunk_ids (list[str]): The chunk identifiers associated with the knowledge node.
        type_name (str): The type name of the knowledge node, this is read-only and present for downstream (de)serialization.
        id (str): The unique identifier of the knowledge node, automatically generated based on name and type.
        data (dict): Additional data associated with the knowledge node.
    """

    name: str = Field(
        description="The name of the knowledge node. Only the combination of name and type has to be unique. For example, 'apple' can be both a noun and a company. The name+type should be unique instead."
    )
    type: str = Field(
        default="Unknown",
        description="The type of the knowledge node. In a property modeled graph this should be an ontology class.",
    )
    type_name: str = Field(
        default="KnwlNode",
        frozen=True,
        description="The type name of the knowledge node for (de)serialization purposes.",
    )
    id: Optional[str] = Field(
        default=None,
        description="The unique identifier of the knowledge node, automatically generated from name and type",
    )
    description: str = Field(
        default="",
        description="The content or description which normally comes from the extracted text. This can be used for embedding purposes, together with the name and the type",
    )
    chunk_ids: Optional[list[str]] = Field(
        default_factory=list,
        description="The chunk identifiers associated with the knowledge node.",
    )
    degree: Optional[int] = Field(
        default=None, description="The degree of the knowledge node in the graph."
    )
    keywords: Optional[list[str]] = Field(
        default_factory=list,
        description="Keywords associated with the node. These can be used as types or labels in a property graph. Note that the names of the keywords should ideally be from an ontology.",
    )
    index: int = Field(
        default=0, description="The index of the node within the parent list, if any."
    )
    data: dict = Field(
        default_factory=dict,
        description="Additional data associated with the knowledge node.",
    )

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

    def has_data(self, key: str) -> bool:
        """
        Check if the KnwlNode has any additional data.

        Returns:
            bool: True if the data dictionary is not empty, False otherwise.
        """

        return key in self.data

    def get_data(self, key: str = None):
        """
        Get additional data associated with the KnwlNode.

        Returns:
            The value associated with the key in the data dictionary, or None if the key does not exist.
        """

        if key is None:
            return self.data
        return self.data.get(key, None)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None or len(str.strip(v)) == 0:
            raise ValueError("The name of a KnwlNode cannot be None or empty.")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v is None or len(str.strip(v)) == 0:
            raise ValueError("The type of a KnwlNode cannot be None or empty.")
        return v.strip().replace("<", "").replace(">", "") # sanitize accidents from LLMs

    @model_validator(mode="after")
    def set_id(self) -> "KnwlNode":
        if self.id is None:
            object.__setattr__(self, "id", self.hash_node(self))
        return self

    @staticmethod
    def hash_node(n: "KnwlNode") -> str:
        # name and type form the primary key
        return KnwlNode.hash_keys(n.name, n.type)

    @staticmethod
    def hash_keys(name: str, type: str) -> str:
        return hash_with_prefix(name + " " + type, prefix="node|>")

    def __repr__(self) -> str:
        return f"<KnwlNode, name={self.name}, type={self.type})>"

    def __str__(self) -> str:
        return self.__repr__()

    def to_text(self) -> str:
        return f"""
Type: {self.type}
Name: {self.name}
Description: {self.description}
Keywords: {', '.join(self.keywords) if self.keywords else 'None'}
    """
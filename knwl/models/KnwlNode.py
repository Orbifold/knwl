from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlNode(BaseModel):
    """
    An atom of knowledge.

    Minimum required fields are name and type, the id is a hash of these two fields.
    This is an immutable class, use the update() method to create a new instance with updated fields.

    Attributes:
        name (str): The name of the knowledge node. Can be unique but in a refined model it should not. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.
        type (str): The type of the knowledge node.
        description (str): A description of the knowledge node.
        chunk_ids (List[str]): The chunk identifiers associated with the knowledge node.
        type_name (str): The type name of the knowledge node, this is read-only and present for downstream (de)serialization.
        id (str): The unique identifier of the knowledge node, automatically generated based on name and type.
    """

    name: str = Field(description="The name of the knowledge node. Only the combination of name and type has to be unique. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.")
    type: str = Field(default="Unknown", description="The type of the knowledge node. In a property modeled graph this should be an ontology class.", )
    type_name: str = Field(default="KnwlNode", frozen=True, description="The type name of the knowledge node for (de)serialization purposes.", )
    id: str = Field(default=None, description="The unique identifier of the knowledge node, automatically generated from name and type", init=False, )
    description: str = Field(default="", description="The content or description which normally comes from the extracted text. This can be used for embedding purposes, together with the name and the type", )
    chunk_ids: List[str] = Field(default_factory=list, description="The chunk identifiers associated with the knowledge node.", )

    model_config = {"frozen": True}

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
        return v

    @model_validator(mode="after")
    def set_id(self) -> "KnwlNode":
        object.__setattr__(self, "id", self.hash_node(self))
        return self

    @staticmethod
    def hash_node(n: "KnwlNode") -> str:
        # name and type form the primary key
        return KnwlNode.hash_keys(n.name, n.type)

    @staticmethod
    def hash_keys(name: str, type: str) -> str:
        return hash_with_prefix(name + " " + type, prefix="node|>")

    def update(self, **kwargs) -> "KnwlNode":
        """
        Create a new KnwlNode instance with updated fields. Only 'name', 'type', and 'description' can be updated.
        """
        allowed_fields = {"name", "type", "description"}
        invalid_fields = set(kwargs.keys()) - allowed_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields: {invalid_fields}. Only 'name', 'type', and 'description' are allowed.")
        new_node = self.model_copy(update=kwargs)
        # pydantic does not call the model_validator on model_copy, so we need to set the id manually
        object.__setattr__(new_node, "id", self.hash_node(new_node))
        return new_node

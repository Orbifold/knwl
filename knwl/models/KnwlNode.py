from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlNode(BaseModel):
    """
    A class representing a knowledge node.

    Attributes:
        name (str): The name of the knowledge node. Can be unique but in a refined model it should not. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.
        type (str): The type of the knowledge node.
        description (str): A description of the knowledge node.
        chunkIds (List[str]): The chunk identifiers associated with the knowledge node.
        typeName (str): The type name of the knowledge node, default is "KnwlNode".
        id (str): The unique identifier of the knowledge node, default is a new UUID.
    """
    name: str
    type: str = "UNKNOWN"
    typeName: str = "KnwlNode"
    id: Optional[str] = Field(default=None, description="The unique identifier of the knowledge node")
    description: str = Field(default="", description="A description of the knowledge node")
    chunkIds: List[str] = Field(default=[], description="The chunk identifiers associated with the knowledge node.")

    model_config = {"frozen": True}

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None or len(str.strip(v)) == 0:
            raise ValueError("Content of a KnwlNode cannot be None or empty.")
        return v

    @model_validator(mode='after')
    def set_id(self) -> 'KnwlNode':
        if self.name is not None and len(str.strip(self.name)) > 0:
            object.__setattr__(self, "id", self.hash_node(self))
        else:
            object.__setattr__(self, "id", None)
        return self

    @staticmethod
    def hash_node(n: 'KnwlNode') -> str:
        # name and type form the primary key
        return KnwlNode.hash_keys(n.name, n.type)

    @staticmethod
    def hash_keys(name: str, type: str) -> str:
        return hash_with_prefix(name + " " + type, prefix="node-")

    def update_id(self):
        if self.name is not None and len(str.strip(self.name)) > 0:
            object.__setattr__(self, "id", KnwlNode.hash_node(self))
        else:
            object.__setattr__(self, "id", None)

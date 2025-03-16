from knwl.utils import hash_with_prefix


from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnwlNode:
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
    type: str = field(default="UNKNOWN")
    typeName: str = "KnwlNode"
    id: str = field(default=None)
    description: str = field(default="")
    chunkIds: List[str] = field(default_factory=list)

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

    def __post_init__(self):
        if self.name is None or len(str.strip(self.name)) == 0:
            raise ValueError("Content of a KnwlNode cannot be None or empty.")
        self.update_id()
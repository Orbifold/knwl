from knwl.models.KnwlNode import KnwlNode


from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnwlDegreeNode(KnwlNode):
    """
    A class representing a knowledge node with a degree.

    Attributes:
        name (str): The name of the knowledge node. Can be unique but in a refined model it should not. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.
        type (str): The type of the knowledge node.
        description (str): A description of the knowledge node.
        chunkIds (List[str]): The chunk identifiers associated with the knowledge node.
        degree (int): The degree of the node.
        typeName (str): The type name of the knowledge node, default is "KnwlNode".
        id (str): The unique identifier of the knowledge node, default is a new UUID.
    """
    degree: int = field(default=0)
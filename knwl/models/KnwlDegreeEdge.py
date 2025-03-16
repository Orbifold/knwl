from knwl.models.KnwlEdge import KnwlEdge


from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnwlDegreeEdge(KnwlEdge):
    """
    Represents a knowledge edge in a graph with a degree.

    Attributes:
        sourceId (str): The ID of the source node.
        targetId (str): The ID of the target node.
        chunkIds (str): The ID of the chunk.
        weight (float): The weight of the edge.
        description (str): A description of the edge.
        keywords (List(str)): Keywords associated with the edge.
        typeName (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
        degree (int): The degree of the edge.
    """
    degree: int = field(default=0)
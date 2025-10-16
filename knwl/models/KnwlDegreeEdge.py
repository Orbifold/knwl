from pydantic import Field

from knwl.models.KnwlEdge import KnwlEdge


class KnwlDegreeEdge(KnwlEdge):
    """
    Represents a knowledge edge in a graph with a degree.

    Inherits all attributes from KnwlEdge and adds:
        degree (int): The degree of the edge, default is 0.
    """
    degree: int = Field(default=0, description="The degree of the edge.")
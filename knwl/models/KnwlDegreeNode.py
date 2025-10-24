from pydantic import Field
from warnings import deprecated

from knwl.models.KnwlNode import KnwlNode


@deprecated("V1 remnant - use KnwlNode instead.")
class KnwlDegreeNode(KnwlNode):
    """
    A class representing a knowledge node with a degree.

    Inherits all attributes from KnwlNode and adds:
        degree (int): The degree of the node, default is 0.
    """

    degree: int = Field(default=0, description="The degree of the node.")

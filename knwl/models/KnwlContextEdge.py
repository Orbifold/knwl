from typing import List

from pydantic import BaseModel, Field


class KnwlContextEdge(BaseModel):
    """
    Represents an edge in a RAG (Retrieval-Augmented Generation) graph.
    
    Attributes:
        index (str): The index identifier of the edge.
        id (str): The unique identifier of the edge.
        source (str): The source node identifier.
        target (str): The target node identifier.
        description (str): A description of the relationship.
        keywords (List[str]): Keywords associated with the edge.
        weight (float): The weight or strength of the edge.
        order (int): The order of the edge in the sequence.
    """
    model_config = {"frozen": True}
    
    index: str = Field(description="The index identifier of the edge.")
    id: str = Field(description="The unique identifier of the edge.")
    source: str = Field(description="The source node identifier.")
    target: str = Field(description="The target node identifier.")
    description: str = Field(description="A description of the relationship.")
    keywords: List[str] = Field(description="Keywords associated with the edge.")
    weight: float = Field(description="The weight or strength of the edge.")
    order: int = Field(description="The order of the edge in the sequence.")

    @staticmethod
    def get_header():
        return ["id", "source", "target", "description", "keywords", "weight"]

    def to_row(self):
        return "\t".join(
            [self.index, self.source, self.target, self.description, ", ".join(self.keywords), str(self.weight)]
        )
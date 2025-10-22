from pydantic import BaseModel, Field


class KnwlGragNode(BaseModel):
    """
    Represents a node in a RAG (Retrieval-Augmented Generation) graph.
    
    Attributes:
        id (str): The unique identifier of the node.
        index (str): The index identifier of the node.
        name (str): The name of the node.
        type (str): The type or category of the node.
        description (str): A description of the node.
        order (int): The order of the node in the sequence.
    """
    model_config = {"frozen": True}
    
    id: str = Field(description="The unique identifier of the node.")
    index: str = Field(description="The index identifier of the node.")
    name: str = Field(description="The name of the node.")
    type: str = Field(description="The type or category of the node.")
    description: str = Field(description="A description of the node.")
    order: int = Field(description="The order of the node in the sequence.")

    @staticmethod
    def get_header():
        return ["id", "name", "type", "description", ]

    def to_row(self):
        return "\t".join(
            [self.index, self.name, self.type, self.description]
        )
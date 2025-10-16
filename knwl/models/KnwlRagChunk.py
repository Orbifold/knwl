from pydantic import BaseModel, Field


class KnwlRagChunk(BaseModel):
    """
    Represents a chunk of text used in RAG (Retrieval-Augmented Generation) operations.
    
    Attributes:
        index (str): The index identifier of the chunk.
        text (str): The actual text content of the chunk.
        order (int): The order of the chunk in the sequence.
        id (str): The unique identifier of the chunk.
    """
    model_config = {"frozen": True}
    
    index: str = Field(description="The index identifier of the chunk.")
    text: str = Field(description="The actual text content of the chunk.")
    order: int = Field(description="The order of the chunk in the sequence.")
    id: str = Field(description="The unique identifier of the chunk.")

    @staticmethod
    def get_header():
        return ["id", "content"]

    def to_row(self):
        return "\t".join(
            [self.index, self.text]
        )
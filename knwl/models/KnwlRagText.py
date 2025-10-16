from pydantic import BaseModel, Field


class KnwlRagText(BaseModel):
    """
    Represents text data used in RAG (Retrieval-Augmented Generation) operations.
    
    Attributes:
        index (str): The index identifier of the text.
        text (str): The actual text content.
        order (int): The order of the text in the sequence.
        id (str): The unique identifier of the text.
    """
    model_config = {"frozen": True}
    
    index: str = Field(description="The index identifier of the text.")
    text: str = Field(description="The actual text content.")
    order: int = Field(description="The order of the text in the sequence.")
    id: str = Field(description="The unique identifier of the text.")
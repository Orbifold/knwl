from pydantic import BaseModel, Field


class KnwlGragReference(BaseModel):
    """
    Represents a reference in the RAG (Retrieval-Augmented Generation) system.
    This class holds metadata about a reference, including its index, name, description,
    timestamp, and a unique identifier (id).
    It is used to track and manage references within the context of RAG operations.

    Chunks refer to specific pieces of information or data that are retrieved
    during the RAG process, and references provide additional context or metadata
    about these chunks.
    The `id` is typically a hash of the reference's content, ensuring uniqueness.
    
    Attributes:
        index (str): The index identifier of the reference.
        name (str): The name of the reference.
        description (str): A description of the reference.
        timestamp (str): The timestamp when the reference was created or last modified.
        id (str): The unique identifier of the reference, typically a hash of its content.
    """
    model_config = {"frozen": True}
    
    index: str = Field(description="The index identifier of the reference.")
    name: str = Field(description="The name of the reference.")
    description: str = Field(description="A description of the reference.")
    timestamp: str = Field(description="The timestamp when the reference was created or last modified.")
    id: str = Field(description="The unique identifier of the reference, typically a hash of its content.")

from typing import Optional
from pydantic import BaseModel, Field, model_validator

from knwl.utils import hash_with_prefix


class KnwlReference(BaseModel):
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
    
    index: Optional[int] = Field(default=0,description="The index within the list of references.")
    document_id: str = Field(description="The unique identifier of the document containing the reference.")
    content: Optional[str] = Field(default=None, description="The content of the reference.")
    name: Optional[str] = Field(default=None, description="The name of the reference.")
    description: Optional[str] = Field(default=None, description="A description of the reference.")
    timestamp: Optional[str] = Field(default=None, description="The timestamp when the reference was created or last modified.")
    id: Optional[str] = Field(default=None, description="The unique identifier of the reference, typically a hash of its content.")

    @model_validator(mode="after")
    def set_id(self) -> "KnwlReference":
        if self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(self, "id", KnwlReference.hash_keys(self.content))
        return self

    @staticmethod
    def hash_keys(content: str) -> str:
        return hash_with_prefix(content, prefix="grag-ref|>")

    
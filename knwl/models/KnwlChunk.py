from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from knwl.utils import hash_with_prefix


class KnwlChunk(BaseModel):
    """
    Represents a chunk of text content (aka "knowledge" or "chunk" or "document" in some frameworks), typically derived from a larger document.
    Each chunk has a token count, the actual content, and metadata such as origin ID and
    index within the source document.
    """

    tokens: Optional[int] = Field(
        default=None, description="Number of tokens in the chunk"
    )
    content: str = Field(..., description="The actual content of the chunk")
    origin_id: Optional[str] = Field(None, description="The ID of the origin document")
    index: int = Field(
        default=0, description="The index of the chunk within the source document"
    )
    type_name: str = Field(
        default="KnwlChunk", frozen=True, description="The type name of this class."
    )
    id: Optional[str] = Field(default=None, description="The unique ID of the chunk")

    @field_validator("content")
    def content_not_empty(cls, v):
        if v is None or len(str.strip(v)) == 0:
            raise ValueError("Content of a KnwlChunk cannot be None or empty.")
        return v

    @model_validator(mode="after")
    def set_id(self) -> "KnwlChunk":
        if self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(self, "id", KnwlChunk.hash_keys(self.content))
        return self

    @staticmethod
    def hash_keys(content: str) -> str:
        return hash_with_prefix(content, prefix="chunk|>")

    @staticmethod
    def from_text(text: str) -> "KnwlChunk":
        return KnwlChunk(content=text)

from typing import Optional
from pydantic import BaseModel, Field, Field, model_validator

from knwl.models import KnwlChunk, KnwlGraph
from knwl.models.KnwlDocument import KnwlDocument
from knwl.utils import hash_with_prefix


class KnwlGragIngestion(BaseModel):
    """
    A class representing the result of a Graph RAG ingestion operation."""

    id: Optional[str] = Field(default=None, description="The unique Id of the result.")
    input: KnwlDocument = Field(..., description="The input document for the RAG operation.")
    chunks: Optional[list[KnwlChunk]] = Field(default_factory=list, description="The chunks created from the input document.")
    graph: Optional[KnwlGraph] = Field(default=None, description="The extracted knowledge graph from the input document.")
    @model_validator(mode="after")
    def set_id(self) -> "KnwlGragIngestion":
        if self.id is None:
            object.__setattr__(self, "id", hash_with_prefix(self.input.content, prefix="gragresult|>"))
        return self

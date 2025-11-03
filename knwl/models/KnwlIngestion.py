from typing import Optional
from pydantic import BaseModel, Field, Field, model_validator

from knwl.models import KnwlChunk, KnwlGraph
from knwl.models.KnwlDocument import KnwlDocument
from knwl.utils import hash_with_prefix


class KnwlIngestion(BaseModel):
    """
    A class representing the result of a Graph RAG ingestion operation."""

    id: Optional[str] = Field(default=None, description="The unique Id of the result.")
    input: KnwlDocument = Field(
        ..., description="The input document for the RAG operation."
    )
    chunks: Optional[list[KnwlChunk]] = Field(
        default_factory=list, description="The chunks created from the input document."
    )
    chunk_graphs: Optional[list[KnwlGraph]] = Field(
        default_factory=list,
        description="The knowledge graphs extracted from each chunk.",
    )
    graph: Optional[KnwlGraph] = Field(
        default=None,
        description="The extracted and consolidated knowledge graph from the input document.",
    )
    
    @model_validator(mode="after")
    def set_id(self) -> "KnwlIngestion":
        if self.id is None:
            object.__setattr__(
                self, "id", hash_with_prefix(self.input.content, prefix="gragresult|>")
            )
        return self

    def get_node_ids(self) -> list[str]:
        return [self.graph.get_node_ids() if self.graph else []]

    def get_edge_ids(self) -> list[str]:
        return [self.graph.get_edge_ids() if self.graph else []]

    def get_node_names(self) -> list[str]:
        return [node.name for node in self.graph.nodes] if self.graph else []

    def get_node_types(self) -> list[str]:
        return [node.type for node in self.graph.nodes] if self.graph else []

    def get_node_descriptions(self) -> list[str]:
        return [node.description for node in self.graph.nodes] if self.graph else []

    def __repr__(self) -> str:
        return f"<KnwlIngestion, id={self.id}, num_chunks={len(self.chunks)}, num_chunk_graphs={len(self.chunk_graphs)}, nodes={len(self.graph.nodes) if self.graph else 0}, edges={len(self.graph.edges) if self.graph else 0}>"

    def __str__(self) -> str:
        return self.__repr__()

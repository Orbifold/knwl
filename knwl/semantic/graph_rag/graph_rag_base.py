from abc import ABC, abstractmethod
from typing import List

from knwl.framework_base import FrameworkBase
from knwl.models import (GragParams, KnwlChunk, KnwlGragContext, KnwlGraph, KnwlInput, KnwlGragInput, )
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlGragIngestion import KnwlGragIngestion
from knwl.models.KnwlNode import KnwlNode


class GraphRAGBase(FrameworkBase, ABC):
    @abstractmethod
    async def embed_node(self, node: KnwlNode) -> KnwlNode | None: ...

    @abstractmethod
    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]: ...

    @abstractmethod
    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None: ...

    @abstractmethod
    async def embed_edges(self, edges: List[KnwlEdge]) -> List[KnwlEdge]: ...

    @abstractmethod
    async def ingest(self, input: str | KnwlInput | KnwlDocument) -> KnwlGraph | None:
        """
        Ingest raw text or KnwlInput/KnwlDocument and convert to knowledge graph:
        - Chunk the text if necessary
        - Extract entities and relationships
        - Embed (consolidate) nodes and edges (graph and vector store)
        """
        ...

    @abstractmethod
    async def extract(self, input: str | KnwlInput | KnwlDocument, enable_chunking: bool = True) -> KnwlGragIngestion | None:
        """
        Extract a knowledge graph from raw text or KnwlInput/KnwlDocument.
        This is the same as `ingest` but without embedding (consolidation).
        """
        ...

    @abstractmethod
    async def augment(self, input: str | KnwlInput | KnwlGragInput, params: GragParams = None) -> KnwlGragContext | None:
        """
        Retrieve context from the knowledge graph and augment the input text.
        All you need to answer questions or generate text with context.
        """
        ...

    @abstractmethod
    async def nearest_nodes(self, query: str, query_param: GragParams) -> list[KnwlNode] | None:
        """
        Query nodes from the knowledge graph based on the input query and parameters.
        """
        ...

    @abstractmethod
    async def nearest_edges(self, query: str, query_param: GragParams) -> list[KnwlEdge] | None:
        """
        Query edges from the knowledge graph based on the input query and parameters.
        """
        ...

    @abstractmethod
    async def nearest_chunks(self, query: str, query_param: GragParams) -> list[KnwlChunk] | None:
        """
        Query chunks based on the input query and parameters.
        This does not involve the graph directly but is part of the naive RAG pipeline.
        """
        ...

    @abstractmethod
    async def get_node_by_id(self, node_id: str) -> KnwlNode | None:
        """
        Retrieve a node by its ID from the knowledge graph.
        """
        ...

    @abstractmethod
    async def node_degree(self, node_id: str) -> int:
        """
        Retrieve the degree of a node in the graph.

        Args:
            node_id (str): The unique identifier of the node.

        Returns:
            int: The degree of the node, or 0 if the node does not exist.
        """
        ...

    @abstractmethod
    async def get_attached_edges(self, nodes: List[KnwlNode]) -> List[KnwlEdge]:
        """
        Retrieve the edges attached to the given nodes.

        Args:
            nodes (List[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            List[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        ...

    @abstractmethod
    async def save_sources(self, sources: List[KnwlDocument]) -> bool:
        """
        Save the source documents used for ingestion.
        This is important for traceability and reference but implementation is optional if this operates within a broader system that already manages documents (workflow).

        Args:
            sources (List[KnwlDocument]): A list of KnwlDocument objects representing the source documents.

        Returns:
            bool: True if the sources were saved successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def save_chunks(self, chunks: List[KnwlChunk]) -> bool:
        """
        Save the chunks generated during ingestion.
        This is important for traceability and reference but implementation is optional if this operates within a broader system that already manages text chunks (workflow).

        Args:
            chunks (List[KnwlChunk]): A list of KnwlChunk objects representing the text chunks.

        Returns:
            bool: True if the chunks were saved successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: str) -> KnwlChunk | None:
        """
        Retrieve a chunk by its Id from the chunk storage.
        The implementation of this method is optional depending on whether chunk storage is managed within this system or externally.
        Args:
            chunk_id (str): The unique identifier of the chunk.
        """
        ...

    @abstractmethod
    async def get_source_by_id(self, source_id: str) -> KnwlDocument | None:
        """
        Retrieve a source document by its Id from the source storage.
        The implementation of this method is optional depending on whether source storage is managed within this system or externally.
        """
        ...

    @abstractmethod
    async def edge_degree(self, edge_id: str) -> int:
        ...

    @abstractmethod
    async def edge_degrees(self, edges: list[KnwlEdge]) -> list[int]:
        ...

    @abstractmethod
    async def get_semantic_endpoints(self, edge_ids: list[str]) -> dict[str, tuple[str, str]]:
        ...

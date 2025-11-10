from abc import ABC, abstractmethod
from typing import List

from knwl.framework_base import FrameworkBase
from knwl.models import (
    KnwlParams,
    KnwlChunk,
    KnwlContext,
    KnwlGraph,
    KnwlInput,
    KnwlInput,
)
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlIngestion import KnwlIngestion
from knwl.models.KnwlKeywords import KnwlKeywords
from knwl.models.KnwlNode import KnwlNode


class GraphRAGBase(FrameworkBase, ABC):
    @abstractmethod
    async def embed_node(self, node: KnwlNode) -> KnwlNode | None: ...

    @abstractmethod
    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]: ...

    @abstractmethod
    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None: ...

    @abstractmethod
    async def embed_edges(self, edges: list[KnwlEdge]) -> list[KnwlEdge]: ...

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
    async def extract(
        self, input: str | KnwlInput | KnwlDocument, enable_chunking: bool = True
    ) -> KnwlIngestion | None:
        """
        Extract a knowledge graph from raw text or KnwlInput/KnwlDocument.
        This is the same as `ingest` but without embedding (consolidation).
        """
        ...

    @abstractmethod
    async def extract_keywords(self, input: str | KnwlInput) -> KnwlKeywords | None:
        """
        Extract keywords from the input text.
        These keywords will be used to query the knowledge graph for relevant context.
        The high-level keywords are global topics, main subjects or areas of interest in the text.
        The local keywords are specific entities, concepts, or details mentioned in the text.
        """
        ...

    @abstractmethod
    async def augment(self, input: str | KnwlInput) -> KnwlContext | None:
        """
        Retrieve context from the knowledge graph and augment the input text.
        All you need to answer questions or generate text with context.
        """
        ...

    @abstractmethod
    async def nearest_nodes(
        self, query: str, query_param: KnwlParams
    ) -> list[KnwlNode] | None:
        """
        Query nodes from the knowledge graph based on the input query and parameters.
        """
        ...

    @abstractmethod
    async def nearest_edges(
        self, query: str, params: KnwlParams
    ) -> list[KnwlEdge] | None:
        """
        Query edges from the knowledge graph based on the input query and parameters.
        """
        ...

    @abstractmethod
    async def nearest_chunks(
        self, query: str, params: KnwlParams
    ) -> list[KnwlChunk] | None:
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
    async def get_attached_edges(self, nodes: list[KnwlNode]) -> list[KnwlEdge]:
        """
        Retrieve the edges attached to the given nodes.

        Args:
            nodes (list[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        ...

    @abstractmethod
    async def get_edges_between_nodes(
        self, source_id: str, target_id: str
    ) -> list[KnwlEdge]:
        """
        Retrieve edges between two nodes by their IDs from the knowledge graph.
        """
        ...

    @abstractmethod
    async def save_sources(self, sources: list[KnwlDocument]) -> bool:
        """
        Save the source documents used for ingestion.
        This is important for traceability and reference but implementation is optional if this operates within a broader system that already manages documents (workflow).

        Args:
            sources (list[KnwlDocument]): A list of KnwlDocument objects representing the source documents.

        Returns:
            bool: True if the sources were saved successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def save_chunks(self, chunks: list[KnwlChunk]) -> bool:
        """
        Save the chunks generated during ingestion.
        This is important for traceability and reference but implementation is optional if this operates within a broader system that already manages text chunks (workflow).

        Args:
            chunks (list[KnwlChunk]): A list of KnwlChunk objects representing the text chunks.

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
    async def edge_degree(self, edge_id: str) -> int: ...

    @abstractmethod
    async def assign_edge_degrees(self, edges: list[KnwlEdge]) -> list[int]: ...

    @abstractmethod
    async def get_semantic_endpoints(
        self, edge_ids: list[str]
    ) -> dict[str, tuple[str, str]]: ...

    @abstractmethod
    async def node_exists(self, node_id: str) -> bool:
        """
        Check if a node with the given Id exists in the knowledge graph.
        """
        ...

    @abstractmethod
    async def node_count(self) -> int:
        """
        Get the total number of nodes in the knowledge graph.
        """
        ...

    @abstractmethod
    async def edge_count(self) -> int:
        """
        Get the total number of edges in the knowledge graph.
        """
        ...

    @abstractmethod
    async def delete_node_by_id(self, node_id: str) -> bool:
        """
        Delete a node by its Id from the knowledge graph.
        Returns True if the node was deleted, False if it did not exist.
        """
        ...

    @abstractmethod
    async def chunk(self, document: KnwlDocument) -> list[KnwlChunk]:
        """
        Chunk the given document into smaller KnwlChunk objects.
        """
        ...

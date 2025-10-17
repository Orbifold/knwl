from logging import log
from knwl.di import defaults
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from typing import Any, Dict, List, Optional

from knwl.models import KnwlContext, KnwlEdge, KnwlGraph, KnwlInput, KnwlRagInput
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.services import Services


@defaults("graph_rag")
class GraphRAG(GraphRAGBase):
    """
    A class for performing Graph-based Retrieval-Augmented Generation (RAG) using a knowledge graph.
    This class provides methods to extract knowledge graphs from text, ingest them into a vector store,
    and augment input text with relevant context from the knowledge graph.

    Default implementation of the `GraphRAGBase` abstract base class.
    Methods
    -------
    extract(input: str | KnwlInput | KnwlDocument) -> KnwlGraph | None
        Extract a knowledge graph from raw text or KnwlInput/KnwlDocument.
    ingest(input: str | KnwlInput | KnwlDocument) -> KnwlGraph | None
        Ingest a knowledge graph from raw text or KnwlInput/KnwlDocument into the vector store.
    augment(input: str | KnwlInput | KnwlRagInput) -> KnwlContext | None
        Retrieve context from the knowledge graph and augment the input text.
    """

    def __init__(
        self, semantic_graph: Optional[SemanticGraphBase] = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.semantic_graph = semantic_graph
        if self.semantic_graph is None:
            raise ValueError("GraphRAG: semantic_graph must be provided.")
        if not isinstance(self.semantic_graph, SemanticGraphBase):
            raise ValueError(
                "GraphRAG: semantic_graph must be an instance of SemanticGraphBase."
            )

    async def embed_node(self, node: KnwlNode) -> KnwlNode | None:
        return await self.semantic_graph.embed_node(node)

    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]:
        return await self.semantic_graph.embed_nodes(nodes)

    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None:
        return await self.semantic_graph.embed_edge(edge)

    async def embed_edges(self, edges: List[KnwlEdge]) -> List[KnwlEdge]:
        return await self.semantic_graph.embed_edges(edges)

    async def ingest(self, input: str | KnwlInput | KnwlDocument) -> KnwlGraph | None:
        """
        Ingest raw text or KnwlInput/KnwlDocument and convert to knowledge graph:
        - Chunk the text if necessary
        - Extract entities and relationships
        - Embed (consolidate) nodes and edges (graph and vector store)
        """
        # ============================================================================================
        # Validate input
        # ============================================================================================
        if input is None:
            raise ValueError("GraphRAG: input cannot be None.")
        content_to_ingest = None
        # ============================================================================================
        # Determine content to ingest based on input type
        # ============================================================================================
        if isinstance(input, str):
            content_to_ingest = input
        elif isinstance(input, KnwlInput):
            content_to_ingest = input.content
        elif isinstance(input, KnwlDocument):
            content_to_ingest = input.content
        if content_to_ingest is None or len(content_to_ingest.strip()) == 0:
            raise ValueError("GraphRAG: input content cannot be None or empty.")
        # ============================================================================================
        # Convert input to KnwlDocument
        # ============================================================================================
        document_to_ingest = None
        if isinstance(input, KnwlDocument):
            document_to_ingest = input
        elif isinstance(input, KnwlInput):
            document_to_ingest = KnwlDocument.from_input(input)
        elif isinstance(input, str):
            document_to_ingest = KnwlDocument(content=input)
        await self.save_sources([document_to_ingest])
    async def extract(self, input: str | KnwlInput | KnwlDocument) -> KnwlGraph | None:
        """
        Extract a knowledge graph from raw text or KnwlInput/KnwlDocument.
        This is the same as `ingest` but without embedding (consolidation).
        """
        pass

    async def augment(
        self, input: str | KnwlInput | KnwlRagInput
    ) -> KnwlContext | None:
        """
        Retrieve context from the knowledge graph and augment the input text.
        All you need to answer questions or generate text with context.
        """
        pass

    async def save_sources(self, sources: List[KnwlDocument]) -> bool:
        """
        Save source documents to the vector store.
        """
        if self.semantic_graph is None or not hasattr(
            self.semantic_graph, "save_sources"
        ):
            raise ValueError(
                "GraphRAG: semantic_graph must be provided and have a save_sources method."
            )
        return await self.semantic_graph.save_sources(sources)

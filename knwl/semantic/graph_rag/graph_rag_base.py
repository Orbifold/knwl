from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from knwl.framework_base import FrameworkBase
from knwl.models import GragParams, KnwlContext, KnwlEdge, KnwlGraph, KnwlInput, KnwlRagInput
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
    async def extract(
        self, input: str | KnwlInput | KnwlDocument, enable_chunking: bool = True
    ) -> KnwlGragIngestion | None:
        """
        Extract a knowledge graph from raw text or KnwlInput/KnwlDocument.
        This is the same as `ingest` but without embedding (consolidation).
        """
        ...

    @abstractmethod
    async def augment(
        self, 
        input: str | KnwlInput | KnwlRagInput,
        params: GragParams = None
    ) -> KnwlContext | None:
        """
        Retrieve context from the knowledge graph and augment the input text.
        All you need to answer questions or generate text with context.
        """
        ...

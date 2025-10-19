from logging import log
from knwl.chunking.chunking_base import ChunkingBase
from knwl.di import defaults
from knwl.extraction.graph_extraction_base import GraphExtractionBase
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlGragIngestion import KnwlGragIngestion
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from typing import Any, Dict, List, Optional

from knwl.models import (
    KnwlBlob,
    KnwlContext,
    KnwlEdge,
    KnwlGraph,
    KnwlInput,
    KnwlRagInput,
)
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.services import Services
from knwl.storage.blob_storage_base import BlobStorageBase


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
        self,
        semantic_graph: Optional[SemanticGraphBase] = None,
        blob_storage: Optional[BlobStorageBase] = None,
        chunker: Optional[ChunkingBase] = None,
        graph_extractor: Optional[GraphExtractionBase] = None,
    ):
        super().__init__()
        self.semantic_graph: SemanticGraphBase = semantic_graph
        self.blob_storage: BlobStorageBase = blob_storage
        self.chunker: ChunkingBase = chunker
        self.graph_extractor: GraphExtractionBase = graph_extractor
        self.validate_services()

    def validate_services(self) -> None:
        if self.semantic_graph is None:
            raise ValueError("GraphRAG: semantic_graph must be provided.")
        if not isinstance(self.semantic_graph, SemanticGraphBase):
            raise ValueError(
                "GraphRAG: semantic_graph must be an instance of SemanticGraphBase."
            )

        if self.blob_storage is not None and not isinstance(
            self.blob_storage, BlobStorageBase
        ):
            raise ValueError(
                "GraphRAG: blob_storage must be an instance of BlobStorageBase."
            )
        if self.chunker is None:
            raise ValueError("GraphRAG: chunker must be provided.")
        if not isinstance(self.chunker, ChunkingBase):
            raise ValueError("GraphRAG: chunker must be an instance of ChunkingBase.")

        if self.graph_extractor is None:
            raise ValueError("GraphRAG: graph_extractor must be provided.")
        if not isinstance(self.graph_extractor, GraphExtractionBase):
            raise ValueError(
                "GraphRAG: graph_extractor must be an instance of GraphExtractionBase."
            )

    async def embed_node(self, node: KnwlNode) -> KnwlNode | None:
        return await self.semantic_graph.embed_node(node)

    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]:
        return await self.semantic_graph.embed_nodes(nodes)

    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None:
        return await self.semantic_graph.embed_edge(edge)

    async def embed_edges(self, edges: List[KnwlEdge]) -> List[KnwlEdge]:
        return await self.semantic_graph.embed_edges(edges)

    async def ingest(
        self,
        input: str | KnwlInput | KnwlDocument,
        store_source: bool = False,
        enable_chunking: bool = True,
        store_chunks: bool = False,
    ) -> KnwlGraph | None:
        """
        Ingest raw text or KnwlInput/KnwlDocument and convert to knowledge graph.
        See also the `extract` method which does the same without storing anything.
        """
        result: KnwlGragIngestion = await self.extract(
            input, enable_chunking=enable_chunking
        )
        if result.graph is None:
            log.warn("GraphRAG: No knowledge graph was extracted to ingest.")
            return None

        # ============================================================================================
        # Store source document
        # ============================================================================================
        if store_source:
            if self.blob_storage is None:
                log.warn(
                    "GraphRAG: blob_storage is not configured, cannot store source document."
                )
            else:
                await self.save_sources([result.input])
        # ============================================================================================
        # Store chunks
        # ============================================================================================
        # todo: needs the StorageAdapter here to store in diverse places
        if store_chunks:
            if self.blob_storage is None:
                log.warn(
                    "GraphRAG: blob_storage is not configured, cannot store chunks."
                )
            else:
                chunk_documents: List[KnwlDocument] = []
                for chunk in result.chunks:
                    chunk_doc = KnwlDocument.from_chunk(
                        chunk, source_document_id=result.input.id
                    )
                    chunk_documents.append(chunk_doc)
                await self.save_sources(chunk_documents)
        # ============================================================================================
        # Merge graph into semantic graph
        # ============================================================================================
        # note that the `extract` method already consolidated the data semantically
        await self.semantic_graph.graph.merge(result.graph)
        # ============================================================================================
        # Vectorize nodes and edges
        # ============================================================================================
        await self.semantic_graph.embed_nodes(result.graph.nodes)
        await self.semantic_graph.embed_edges(result.graph.edges)

        return result.graph

    async def extract(
        self, input: str | KnwlInput | KnwlDocument, enable_chunking: bool = True
    ) -> KnwlGragIngestion | None:
        """
        Extract a knowledge graph from raw text or KnwlInput/KnwlDocument.
        This is the same as `ingest` but without storing anything.
        """
        # ============================================================================================
        # Validate input
        # ============================================================================================
        if input is None:
            raise ValueError("GraphRAG: input cannot be None.")

        # ============================================================================================
        # Convert input to KnwlDocument
        # ============================================================================================
        document_to_ingest: KnwlDocument = None
        if isinstance(input, KnwlDocument):
            document_to_ingest = input
        elif isinstance(input, KnwlInput):
            document_to_ingest = KnwlDocument.from_input(input)
        elif isinstance(input, str):
            document_to_ingest = KnwlDocument(content=input)
        result = KnwlGragIngestion(input=document_to_ingest)

        # ============================================================================================
        # Chunking
        # ============================================================================================
        if enable_chunking:
            chunks: List[KnwlChunk] = await self.chunker.chunk(
                document_to_ingest.content, source_key=document_to_ingest.id
            )
        else:
            chunks = [KnwlChunk(content=document_to_ingest.content)]
        if len(chunks) == 0:
            log.warn("GraphRAG: No chunks were created from the input document.")
            return result
        result.chunks = chunks
        # ============================================================================================
        # Extract knowledge graph from chunks
        # ============================================================================================
        # merge graphs from all chunks
        extracted_graph: KnwlGraph = None
        for chunk in chunks:
            chunk_graph = await self.graph_extractor.extract_graph(chunk.content)
            result.chunk_graphs.append(chunk_graph)
            if chunk_graph is not None:
                # semantic merge into KG
                if extracted_graph is None:
                    extracted_graph = chunk_graph
                else:
                    # this is not a semantic merge but a simple concatenation in order to return the end result
                    extracted_graph = await self.semantic_graph.consolidate_graphs(
                        extracted_graph, chunk_graph
                    )

        if extracted_graph is None:
            log.warn(
                "GraphRAG: No knowledge graph was extracted from the input document."
            )
            return result
        result.graph = extracted_graph
        return result

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
        # saving originals is optional
        if self.blob_storage is None:
            return False
        for source in sources:
            blob = KnwlBlob.from_document(source)
            await self.blob_storage.upsert(blob)
        return True

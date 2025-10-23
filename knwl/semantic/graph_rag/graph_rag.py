from logging import log


from knwl.chunking.chunking_base import ChunkingBase
from knwl.di import defaults
from knwl.extraction.graph_extraction_base import GraphExtractionBase
from knwl.models import (
    GragParams,
    KnwlBlob,
    KnwlGragContext,
    KnwlGraph,
    KnwlInput,
    KnwlGragInput,
)
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlGragIngestion import KnwlGragIngestion
from knwl.models.KnwlNode import KnwlNode
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.local_strategy import LocalGragStrategy
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.semantic.rag.rag_base import RagBase
from knwl.storage.blob_storage_base import BlobStorageBase
from knwl.storage.storage_base import StorageBase


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
        semantic_graph: SemanticGraphBase | None = None,
        chunk_storage: StorageBase | None = None,
        document_storage: StorageBase | None = None,
        rag_storage: RagBase | None = None,
        graph_extractor: GraphExtractionBase | None = None,
    ):
        super().__init__()
        self.semantic_graph: SemanticGraphBase = semantic_graph
        self.chunk_storage: StorageBase = chunk_storage
        self.document_storage: StorageBase = document_storage
        self.rag_storage: RagBase = rag_storage
        self.graph_extractor: GraphExtractionBase = graph_extractor
        self.validate_services()

    def validate_services(self) -> None:
        if self.semantic_graph is None:
            raise ValueError("GraphRAG: semantic_graph must be provided.")
        if not isinstance(self.semantic_graph, SemanticGraphBase):
            raise ValueError(
                "GraphRAG: semantic_graph must be an instance of SemanticGraphBase."
            )

        if self.chunk_storage is not None and not isinstance(
            self.chunk_storage, BlobStorageBase
        ):
            raise ValueError(
                "GraphRAG: blob_storage must be an instance of BlobStorageBase."
            )
        if self.rag_store is None:
            raise ValueError("GraphRAG: chunker must be provided.")
        if not isinstance(self.rag_store, ChunkingBase):
            raise ValueError("GraphRAG: chunker must be an instance of ChunkingBase.")

        if self.graph_extractor is None:
            raise ValueError("GraphRAG: graph_extractor must be provided.")
        if not isinstance(self.graph_extractor, GraphExtractionBase):
            raise ValueError(
                "GraphRAG: graph_extractor must be an instance of GraphExtractionBase."
            )

    async def edge_degree(self, edge_id: str) -> int:
        return await self.semantic_graph.edge_degree(edge_id)

    async def edge_degrees(self, edges: list[KnwlEdge]) -> list[int]:
        return await self.semantic_graph.edge_degrees(edges)

    async def get_semantic_endpoints(
        self, edge_ids: list[str]
    ) -> dict[str, tuple[str, str]]:
        return await self.semantic_graph.get_semantic_endpoints(edge_ids)

    async def node_degree(self, node_id: str) -> int:
        return await self.semantic_graph.node_degree(node_id)

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
            if self.chunk_storage is None:
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
            if self.chunk_storage is None:
                log.warn(
                    "GraphRAG: blob_storage is not configured, cannot store chunks."
                )
            else:
                self.save_chunks(result.chunks)
        # ============================================================================================
        # Merge graph into semantic graph
        # ============================================================================================
        # note that the `extract` method already consolidated the data semantically
        node_dicts = [n.model_dump() for n in result.graph.nodes]
        edge_dicts = [e.model_dump() for e in result.graph.edges]
        await self.semantic_graph.graph.merge(node_dicts, edge_dicts)
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
            chunks: List[KnwlChunk] = await self.rag_store.chunk(
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
            # add reference to the chunk
            for node in chunk_graph.nodes:
                node.chunk_ids.append(chunk.id)
            for edge in chunk_graph.edges:
                edge.chunk_ids.append(chunk.id)
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
        # ============================================================================================
        # Validate and clean extracted graph
        # ============================================================================================
        # Remove self-loops (edges where source == target)
        cleanup_edges = [
            edge for edge in extracted_graph.edges if edge.source_id != edge.target_id
        ]
        # ensure unique chunk_ids
        for node in extracted_graph.nodes:
            node.chunk_ids = list(set(node.chunk_ids))

        # Remove duplicate edges (same source, target, and type)
        seen_edges = set()
        unique_edges = []
        for edge in cleanup_edges:
            edge_key = (edge.source_id, edge.target_id, edge.type)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)
        for edge in unique_edges:
            edge.chunk_ids = list(set(edge.chunk_ids))
        result.graph = KnwlGraph(
            nodes=extracted_graph.nodes,
            edges=unique_edges,
            keywords=extracted_graph.keywords,
        )
        return result

    async def augment(
        self, input: str | KnwlInput | KnwlGragInput, params: GragParams = None
    ) -> KnwlGragContext | None:
        """
        Retrieve context from the knowledge graph and augment the input text.
        All you need to answer questions or generate text with context.
        """

        if params is None:
            query_params = GragParams()
        if isinstance(input, str):
            grag_input = KnwlGragInput(text=input, params=query_params)
        elif isinstance(input, KnwlGragInput):
            grag_input = input
            query_params = grag_input.params
        elif isinstance(input, KnwlInput):
            grag_input = KnwlGragInput(text=input.text, params=query_params)
        else:
            raise ValueError(
                "GraphRAG: input must be of type str, KnwlInput, or KnwlRagInput."
            )

        strategy = self.get_strategy(grag_input)
        return await strategy.augment(grag_input)

    def get_strategy(self, input: KnwlGragInput) -> "GragStrategyBase":
        """
        Get the appropriate strategy based on the input type.
        """
        mode = input.params.mode
        if mode == "local":
            return LocalGragStrategy(self)
        else:
            raise ValueError(f"GraphRAG: Unknown strategy mode '{mode}'.")

    async def save_sources(self, sources: List[KnwlDocument]) -> bool:
        """
        Save source documents to the vector store.
        """
        # saving originals is optional
        if self.chunk_storage is None:
            return False
        for source in sources:
            blob = KnwlBlob.from_document(source)
            await self.chunk_storage.upsert(blob)
        return True

    async def nearest_nodes(self, query: str, top_k: int = 5) -> list[KnwlNode] | None:
        """
        Query nodes from the knowledge graph based on the input query and parameters.
        """
        return await self.semantic_graph.nearest_nodes(query, top_k)

    async def get_node_by_id(self, id: str) -> KnwlNode | None:
        """
        Retrieve a node by its ID from the knowledge graph.
        """
        return await self.semantic_graph.get_node_by_id(id)

    async def nearest_edges(self, query: str, top_k: int = 5) -> list[KnwlEdge] | None:
        """
        Query edges from the knowledge graph based on the input query and parameters.
        """
        return await self.semantic_graph.nearest_edges(query, top_k)

    async def get_attached_edges(self, nodes: list[KnwlNode]) -> list[KnwlEdge]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (List[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            List[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])

        return await self.semantic_graph.get_attached_edges(nodes)

    async def save_chunks(self, chunks: List[KnwlChunk]) -> bool:
        """
        Save chunks to the blob storage.
        """
        # saving chunks is optional
        if self.chunk_storage is None:
            return False
        for chunk in chunks:
            blob = KnwlBlob.from_chunk(chunk)
            # todo: use StorageAdapter here
            await self.chunk_storage.upsert(blob)
        return True

    async def get_chunk_by_id(self, chunk_id: str) -> KnwlChunk | None:
        """
        Retrieve a chunk by its Id from the chunk storage.
        The implementation of this method is optional depending on whether chunk storage is managed within this system or externally.
        Args:
            chunk_id (str): The unique identifier of the chunk.
        """
        if self.chunk_storage is None:
            return None
        blob: KnwlBlob = await self.chunk_storage.get_by_id(chunk_id)
        if blob is None:
            return None
        chunk = KnwlChunk(
            id=blob.id,
            data=blob.data,
            name=blob.name,
            description=blob.description,
            origin_id=blob.metadata.get("origin_id") if blob.metadata else None,
            index=blob.metadata.get("index") if blob.metadata else None,
            chunk_id=blob.metadata.get("chunk_id") if blob.metadata else None,
            timestamp=blob.timestamp,
        )
        return chunk

    async def get_source_by_id(self, source_id: str) -> KnwlDocument | None:
        """
        Retrieve a source document by its Id from the source storage.
        """
        if self.chunk_storage is None:
            return None
        blob: KnwlBlob = await self.chunk_storage.get_by_id(source_id)
        if blob is None:
            return None
        document = KnwlDocument(
            id=blob.id,
            content=blob.data.decode("utf-8"),
            name=blob.name,
            description=blob.description,
            timestamp=blob.timestamp,
        )
        return document

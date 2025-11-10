from typing import cast

from knwl.chunking.chunking_base import ChunkingBase
from knwl.di import defaults
from knwl.extraction.graph_extraction_base import GraphExtractionBase
from knwl.extraction.keywords_extraction_base import KeywordsExtractionBase
from knwl.logging import log
from knwl.models import (KnwlParams, KnwlContext, KnwlGraph, KnwlInput, )
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlIngestion import KnwlIngestion
from knwl.models.KnwlKeywords import KnwlKeywords
from knwl.models.KnwlNode import KnwlNode
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.global_strategy import GlobalGragStrategy
from knwl.semantic.graph_rag.strategies.hybrid_strategy import HybridGragStrategy
from knwl.semantic.graph_rag.strategies.local_strategy import LocalGragStrategy
from knwl.semantic.graph_rag.strategies.naive_strategy import NaiveGragStrategy
from knwl.semantic.graph_rag.strategies.self_strategy import SelfGragStrategy
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.semantic.rag.rag_base import RagBase


@defaults("graph_rag")
class GraphRAG(GraphRAGBase):
    """
    A class for performing Graph-based Retrieval-Augmented Generation (RAG) using a knowledge graph.
    This class provides methods to extract knowledge graphs from text, ingest them into a vector store,
    and augment input text with relevant context from the knowledge graph.

    Default implementation of the `GraphRAGBase` abstract base class.

    """

    def __init__(self, semantic_graph: SemanticGraphBase | None = None, ragger: RagBase | ChunkingBase | None = None, graph_extractor: GraphExtractionBase | None = None, keywords_extractor: KeywordsExtractionBase | None = None, ):
        super().__init__()
        self.semantic_graph: SemanticGraphBase = semantic_graph
        self.ragger: RagBase | ChunkingBase = ragger
        self.graph_extractor: GraphExtractionBase = graph_extractor
        self.keywords_extractor: KeywordsExtractionBase = keywords_extractor
        self.validate_services()

    def validate_services(self) -> None:
        if self.semantic_graph is None:
            raise ValueError("GraphRAG: semantic_graph must be provided.")
        if not isinstance(self.semantic_graph, SemanticGraphBase):
            raise ValueError("GraphRAG: semantic_graph must be an instance of SemanticGraphBase.")

        if self.ragger is None:
            log.warn("GraphRAG: ragger (RAG store) is not provided. Chunnking and storing will be disabled.")
        else:
            if not isinstance(self.ragger, RagBase) and not isinstance(self.ragger, ChunkingBase):
                raise ValueError("GraphRAG: ragger must be an instance of RagBase or ChunkingBase.")
        if self.graph_extractor is None:
            raise ValueError("GraphRAG: graph_extractor must be provided.")
        if not isinstance(self.graph_extractor, GraphExtractionBase):
            raise ValueError("GraphRAG: graph_extractor must be an instance of GraphExtractionBase.")
        if self.keywords_extractor is not None and not isinstance(self.keywords_extractor, KeywordsExtractionBase):
            raise ValueError("GraphRAG: keywords_extractor, if provided, must be an instance of KeywordsExtractionBase.")

    async def edge_degree(self, edge_id: str) -> int:
        return await self.semantic_graph.edge_degree(edge_id)

    async def assign_edge_degrees(self, edges: list[KnwlEdge]) -> list[int]:
        return await self.semantic_graph.assign_edge_degrees(edges)

    async def get_semantic_endpoints(self, edge_ids: list[str]) -> dict[str, tuple[str, str]]:
        return await self.semantic_graph.get_semantic_endpoints(edge_ids)

    async def node_degree(self, node_id: str) -> int:
        return await self.semantic_graph.node_degree(node_id)

    async def embed_node(self, node: KnwlNode) -> KnwlNode | None:
        return await self.semantic_graph.embed_node(node)

    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]:
        return await self.semantic_graph.embed_nodes(nodes)

    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None:
        return await self.semantic_graph.embed_edge(edge)

    async def embed_edges(self, edges: list[KnwlEdge]) -> list[KnwlEdge]:
        return await self.semantic_graph.embed_edges(edges)

    async def ingest(self, input: str | KnwlInput | KnwlDocument, ) -> KnwlGraph | None:
        """
        Ingest raw text or KnwlInput/KnwlDocument and convert to knowledge graph.
        See also the `extract` method which does the same without storing anything.
        """
        result: KnwlIngestion = await self.extract(input)
        if result.graph is None:
            log.warn("GraphRAG: No knowledge graph was extracted to ingest.")
            return None

        # ============================================================================================
        # Store source document
        # ============================================================================================
        if self.ragger:
            await self.ragger.upsert_document(result.input)

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

    async def chunk(self, document: KnwlDocument) -> list[KnwlChunk]:
        """
        Chunk the document using the provided ragger (ChunkingBase or RagBase).
        """

        if self.ragger is None:
            log.warn("GraphRAG: attempt to chunk but no ragger (ChunkingBase or RagBase instance) is provided.")
            return [KnwlChunk(content=document.content, origin_id=document.id)]
        if isinstance(self.ragger, ChunkingBase):
            chunker = cast(ChunkingBase, self.ragger)
            return await chunker.chunk(document.content, document.id)
        elif isinstance(self.ragger, RagBase):
            chunker = cast(RagBase, self.ragger)
            return await chunker.chunk(document)
        else:
            raise ValueError(f"GraphRAG: provided ragger of type '{type(self.ragger)}' is not supported.")

    async def extract(self, input: str | KnwlInput | KnwlDocument) -> KnwlIngestion | None:
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
        result = KnwlIngestion(input=document_to_ingest)

        # ============================================================================================
        # Chunking
        # ============================================================================================

        result.chunks = await self.chunk(document_to_ingest)

        # ============================================================================================
        # Extract knowledge graph from chunks
        # ============================================================================================
        # merge graphs from all chunks
        extracted_graph: KnwlGraph = None
        for chunk in result.chunks:
            chunk_graph = await self.graph_extractor.extract_graph(chunk.content, chunk_id=chunk.id)
            # # add reference to the chunk
            # for node in chunk_graph.nodes:
            #     node.chunk_ids.append(chunk.id)
            # for edge in chunk_graph.edges:
            #     edge.chunk_ids.append(chunk.id)
            result.chunk_graphs.append(chunk_graph)
            if chunk_graph is not None:
                # semantic merge into KG
                if extracted_graph is None:
                    extracted_graph = chunk_graph
                else:
                    # this is not a semantic merge but a simple concatenation in order to return the end result
                    extracted_graph = await self.semantic_graph.consolidate_graphs(extracted_graph, chunk_graph)

        if extracted_graph is None:
            log.warn("GraphRAG: No knowledge graph was extracted from the input document.")
            return result
        # ============================================================================================
        # Validate and clean extracted graph
        # ============================================================================================
        # Remove self-loops (edges where source == target)
        cleanup_edges = [edge for edge in extracted_graph.edges if edge.source_id != edge.target_id]
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
        result.graph = KnwlGraph(nodes=extracted_graph.nodes, edges=unique_edges, keywords=extracted_graph.keywords, )
        return result

    async def augment(self, input: str | KnwlInput) -> KnwlContext | None:
        """
        Retrieve context from the knowledge graph and augment the input text.
        All you need to answer questions or generate text with context.
        """

        if input is None:
            raise ValueError("GraphRAG: input cannot be None.")
        if isinstance(input, str):
            grag_input = KnwlInput(text=input)
        elif isinstance(input, KnwlInput):
            grag_input = input

        else:
            raise ValueError("GraphRAG: input must be of type str, KnwlInput, or KnwlRagInput.")

        strategy = self.get_strategy(grag_input)
        return await strategy.augment(grag_input)

    def get_strategy(self, input: KnwlInput) -> "GragStrategyBase":
        """
        Get the appropriate strategy based on the specified mode in the input parameters.
        """
        mode = input.params.strategy
        if mode == "local":
            return LocalGragStrategy(self)
        elif mode == "naive":
            return NaiveGragStrategy(self)
        elif mode == "hybrid":
            return HybridGragStrategy(self)
        elif mode == "global":
            return GlobalGragStrategy(self)
        elif mode == "none" or mode == "self":
            return SelfGragStrategy(self)
        else:
            raise ValueError(f"GraphRAG: Unknown strategy mode '{mode}'.")

    async def nearest_nodes(self, query: str, params: KnwlParams) -> list[KnwlNode] | None:
        """
        Query nodes from the knowledge graph based on the input query and parameters.
        """
        return await self.semantic_graph.nearest_nodes(query, params.top_k)

    async def get_node_by_id(self, id: str) -> KnwlNode | None:
        """
        Retrieve a node by its ID from the knowledge graph.
        """
        return await self.semantic_graph.get_node_by_id(id)

    async def nearest_edges(self, query: str, params: KnwlParams) -> list[KnwlEdge] | None:
        """
        Query edges from the knowledge graph based on the input query and parameters.
        """
        return await self.semantic_graph.nearest_edges(query, params.top_k)

    async def get_attached_edges(self, nodes: list[KnwlNode]) -> list[KnwlEdge]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (list[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            list[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])

        return await self.semantic_graph.get_attached_edges(nodes)
    async def get_edges_between_nodes(self, source_id: str, target_id: str) -> list[KnwlEdge]:
        """
        Retrieve edges between two nodes by their IDs from the knowledge graph.
        """
        return await self.semantic_graph.get_edges_between_nodes(source_id, target_id)
    
    async def get_chunk_by_id(self, chunk_id: str) -> KnwlChunk | None:
        """
        Retrieve a chunk by its Id from the chunk storage.
        The implementation of this method is optional depending on whether chunk storage is managed within this system or externally.
        Args:
            chunk_id (str): The unique identifier of the chunk.
        """
        if self.ragger is None:
            return None
        else:
            if isinstance(self.ragger, ChunkingBase):
                return None
            elif isinstance(self.ragger, RagBase):
                return await cast(RagBase, self.ragger).get_chunk_by_id(chunk_id)
            else:
                raise ValueError(f"GraphRAG: provided ragger of type '{type(self.ragger)}' is not supported.")

    async def get_source_by_id(self, source_id: str) -> KnwlDocument | None:
        """
        Retrieve a source document by its Id from the source storage.
        """
        if self.ragger is None:
            return None
        else:
            if isinstance(self.ragger, ChunkingBase):
                return None
            elif isinstance(self.ragger, RagBase):
                return await cast(RagBase, self.ragger).get_document_by_id(source_id)
            else:
                raise ValueError(f"GraphRAG: provided ragger of type '{type(self.ragger)}' is not supported.")

    async def save_sources(self, sources: list[KnwlDocument]) -> bool:
        for source in sources:
            await self.ragger.upsert_document(source)
        return True

    async def save_chunks(self, chunks: list[KnwlChunk]) -> bool:
        for chunk in chunks:
            await self.ragger.upsert_chunk(chunk)
        return True

    async def nearest_chunks(self, query: str, query_param: KnwlParams) -> list[KnwlChunk] | None:
        """
        Query chunks based on the input query and parameters.
        This does not involve the graph directly but is part of the naive RAG pipeline.
        """
        if self.ragger is None:
            raise ValueError("GraphRAG: attempt to query chunks but no ragger (ChunkingBase or RagBase instance) is provided.")
        else:
            if isinstance(self.ragger, ChunkingBase):
                raise ValueError("GraphRAG: attempt to query chunks but ragger is a ChunkingBase instance, which does not support semantic querying.")
            elif isinstance(self.ragger, RagBase):
                ragger = cast(RagBase, self.ragger)
                return await ragger.nearest(query, query_param.top_k)
            else:
                raise ValueError(f"GraphRAG: provided ragger of type '{type(self.ragger)}' is not supported.")

    async def extract_keywords(self, input: str | KnwlInput) -> KnwlKeywords | None:
        if self.keywords_extractor is None:
            raise ValueError("GraphRAG: attempt to extract keywords but no keywords_extractor is provided.")
        if isinstance(input, str):
            text = input
        elif isinstance(input, KnwlInput):
            text = input.text
        elif isinstance(input, KnwlInput):
            text = input.text
        else:
            raise ValueError("GraphRAG: input must be of type str, KnwlInput, or KnwlInput.")
        return await self.keywords_extractor.extract(text)

    async def node_exists(self, node_id: str) -> bool:
        """
        Check if a node with the given Id exists in the knowledge graph.
        """
        return await self.semantic_graph.node_exists(node_id)

    async def node_count(self) -> int:
        """
        Get the total number of nodes in the knowledge graph.
        """
        return await self.semantic_graph.node_count()

    async def edge_count(self) -> int:
        """
        Get the total number of edges in the knowledge graph.
        """
        return await self.semantic_graph.edge_count()

    async def delete_node_by_id(self, node_id: str) -> bool:
        """
        Delete a node by its Id from the knowledge graph.
        Returns True if the node was deleted, False if it did not exist.
        """
        return await self.semantic_graph.delete_node_by_id(node_id)

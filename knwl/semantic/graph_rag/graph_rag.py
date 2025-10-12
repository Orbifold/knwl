from logging import log
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from typing import Any, Dict, List, Optional

from knwl.models import KnwlContext, KnwlEdge, KnwlGraph, KnwlInput, KnwlRagInput
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.services import Services

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        specs = Services.get_service_specs("semantic", override=config)
        if specs is None:
            log.error("No semantic graph service configured.")
            raise ValueError("No semantic graph service configured.")
        self.semantic_store:SemanticGraphBase = self.get_service
from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlNode, KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph


class SemanticGraphBase(FrameworkBase, ABC):
    """
    Base class for semantic graph implementations.

    Graph store is just a storage backend for nodes and edges.
    A semantic graph also has
    - embeddings for nodes and edges
    - merges nodes/edges by combining multiple descriptions via LLMs
    - similarity search via embeddings

    You can do embeddings in various graph stores (e.g. Neo4j, TigerGraph, etc.) but the augmentation of description is something you do not have in those graph stores.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def embed_node(self, node: KnwlNode):
        """
        Embed a knowledge node into the semantic graph.

        This method processes a KnwlNode and generates its semantic embedding,
        which can be used for similarity searches, clustering, and other
        semantic operations within the graph structure.

        Args:
            node (KnwlNode): The knowledge node to be embedded into the semantic graph.
                             Contains the content and metadata that will be processed
                             to generate the embedding representation.

        Returns:
            None: This method operates asynchronously and modifies the node's
                  embedding properties in place.

        Raises:
            NotImplementedError: This is a base method that must be implemented
                                by concrete subclasses.
        """
        pass
    @abstractmethod
    async def embed_nodes(self, nodes: list[KnwlNode]):
        pass

    @abstractmethod
    async def embed_edge(self, edge: KnwlEdge):
        pass

    @abstractmethod
    async def embed_edges(self, edge: list[KnwlEdge]):
        pass

    @abstractmethod
    async def merge_graph(self, graph: KnwlGraph):
        pass

    @abstractmethod
    async def get_similar_nodes(self, node: KnwlNode, top_k: int = 5) -> list[KnwlNode]:
        pass

    @abstractmethod
    async def get_similar_edges(self, edge: KnwlEdge, top_k: int = 5) -> list[KnwlEdge]:
        pass
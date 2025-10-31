import copy
from typing import Optional
from knwl import services, KnwlIngestion, KnwlInput, GraphRAG, KnwlAnswer
from knwl.config import (
    get_config,
    get_space_config,
    resolve_config,
    resolve_dict,
    set_active_config,
)
from knwl.llm.llm_base import LLMBase
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph
from knwl.models.KnwlNode import KnwlNode
from knwl.models.KnwlParams import AugmentationStrategy
from types import MappingProxyType


class Knwl:
    """
    This class defines an easy to use gateway to create and consume a knowledge graph.
    It's not a comprehensive API of what Knwl has to offer, merely a simple entry point for common use cases.
    The default configuration behind this API stores everything under the user's home directory in a '.knwl' folder. There is an extensive configuration and dependency injection system behind Knwl that can be used to customize its behavior, but this class abstracts most of that away for simple use cases. It's an invitation to explore the rest of Knwl's capabilities.
    """

    def __init__(self, space: str = "default"):
        """
        Initialize Knwl with optionally the name of knowledge space.
        """
        self._llm = None
        self._space = space
        self._config = get_space_config(space)
        set_active_config(self._config)  # override the whole config
        self.grag: GraphRAG = (
            GraphRAG()
        )  # grag is not a typo but an acronym for Graph RAG

    @property
    def space(self):
        """
        Get the current knowledge space name.
        This is the directory under which the knowledge graph and config are stored, typically '~/.knwl/<space>'.
        """
        return self._space

    @property
    def config(self):
        """
        Get the config for the current knowledge space as a read-only dict.
        """
        cloned = copy.deepcopy(self._config)
        return resolve_dict(
            cloned, config=cloned
        )  # Resolve any references and redirects

    @property
    def llm(self) -> LLMBase:
        """
        Get the LLM client used by Knwl.
        """
        if self._llm is None:
            self._llm = services.get_service("llm")
        return self._llm

    async def add(self, input: str | KnwlInput) -> KnwlIngestion:
        """
        Add input to be processed by Knwl, i.e. ingest the given text or KnwlInput object.
        """
        if isinstance(input, str):
            input = KnwlInput(text=input)
        return await self.grag.ingest(input)

    async def ask(
        self, question: str, strategy: AugmentationStrategy = None
    ) -> KnwlAnswer:
        """ """
        if strategy is None:
            return await self._simple_ask(question)

    async def add_fact(
        self,
        name: str,
        content: str,
        id: Optional[str] = None,
    ) -> KnwlNode:
        """
        Add a single node-fact to the knowledge graph.
        This effectively merges a mini-ingestion of a single node into the graph.
        """
        node = KnwlNode(
            id=id,
            name=name,
            description=content,
        )
        return await self.grag.embed_node(node)

    async def node_exists(self, node_id: str) -> bool:
        """
        Check if a node with the given Id exists in the knowledge graph.
        """

        return await self.grag.node_exists(node_id)

    async def node_count(self) -> int:
        """
        Get the total number of nodes in the knowledge graph.
        """
        return await self.grag.node_count()

    async def edge_count(self) -> int:
        """
        Get the total number of edges in the knowledge graph.
        """
        return await self.grag.edge_count()

    async def get_nodes_by_name(self, node_name: str) -> list[KnwlNode]:
        """
        Get all nodes with the given name from the knowledge graph.
        """
        return await self.grag.semantic_graph.get_nodes_by_name(node_name)

    async def connect(
        self,
        source_name: str,
        target_name: str,
        relation: str,
    ) -> KnwlEdge:
        """
        Connect two nodes in the knowledge graph with a relation.
        This is a simplified method of the `semantic_graph` API.
        """
        if source_name is None or target_name is None:
            raise ValueError("Source and target node names must be provided.")
        if str(source_name).strip() == "" or str(target_name).strip() == "":
            raise ValueError("Source and target node names must be non-empty.")
        if source_name == target_name:
            raise ValueError("Source and target nodes must be different.")

        sources = await self.grag.semantic_graph.get_nodes_by_name(source_name)
        targets = await self.grag.semantic_graph.get_nodes_by_name(target_name)
        if len(sources) == 0:
            raise ValueError(f"No nodes found with name '{source_name}'.")
        if len(targets) == 0:
            raise ValueError(f"No nodes found with name '{target_name}'.")
        # for convenience, just take the first found node with the given name
        source = sources[0]
        target = targets[0]
        edge = KnwlEdge(
            source_id=source.id,
            target_id=target.id,
            description=relation,
            type="Relation",
        )
        return await self.grag.semantic_graph.embed_edge(edge) # embed, not upsert!, this is a semantic store

    async def get_config(self, *keys):
        """
        Get a config value for the current knowledge space by keys.
        For instance, to get the graph path, use `get_config("graph", "user", "path")` or `get_config("@/graph/user/path")`.
        """
        return get_config(*keys)

    async def _simple_ask(self, question: str) -> KnwlAnswer:
        """
        Simple LLM QA without knowledge graph.
        This uses the default LLM service configured.
        """
        found = await self.llm.ask(question)
        return found or KnwlAnswer.none()

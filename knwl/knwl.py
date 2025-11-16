import copy
from enum import Enum
from typing import Optional

from knwl import prompts, services, KnwlInput, GraphRAG, KnwlAnswer, KnwlContext
from knwl.config import (get_config, get_custom_config, resolve_dict, set_active_config, )
from knwl.llm.llm_base import LLMBase
from knwl.models import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph
from knwl.models.KnwlNode import KnwlNode
from knwl.services import Services


class PromptType(Enum):
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    RAG = "rag"
    CONSTANTS = "constants"


class Knwl:
    """
    This class defines an easy to use gateway to create and consume a knowledge graph.
    It's not a comprehensive API of what Knwl has to offer, merely a simple entry point for common use cases.
    The default configuration behind this API stores everything under the user's home directory in a '.knwl' folder. There is an extensive configuration and dependency injection system behind Knwl that can be used to customize its behavior, but this class abstracts most of that away for simple use cases. It's an invitation to explore the rest of Knwl's capabilities.
    """

    def __init__(self, namespace: str = "default", llm: Optional[str] = None, model: Optional[str] = None, override: Optional[dict] = None, ):
        """
        Initialize Knwl with optionally the name of knowledge space.
        """
        self._llm_provider = (llm or "ollama")  # makes Ollama the default LLM provider within this class, but not for Kwnl as a framework
        self._model = model
        self._llm = None
        self._namespace = namespace

        self._config = get_custom_config(namespace, llm_provider=llm, llm_model=model, override=override)
        set_active_config(self._config)  # override the whole config
        # tricky thing here: if you use multiple Knwl instances they will share the singletons if accessed via a single global Services instance
        services = Services()
        self.grag: GraphRAG = services.create_service("graph_rag")  # grag is not a typo but an acronym for Graph RAG

    @property
    def namespace(self):
        """
        Get the current knowledge space name.
        This is the directory under which the knowledge graph and config are stored, typically '~/.knwl/<namespace>'.
        """
        return self._namespace

    @property
    def config(self):
        """
        Get the config for the current knowledge space as a read-only dict.
        """
        cloned = copy.deepcopy(self._config)
        return resolve_dict(cloned, config=cloned)  # Resolve any references and redirects

    @property
    def llm(self) -> LLMBase:
        """
        Get the LLM client used by Knwl.
        """
        if self._llm is None:
            try:
                if self._model:
                    config = {"llm": {f"{self._llm_provider}": {"model": self._model}}}
                    self._llm = services.get_service(f"@/llm/{self._llm_provider}", override=config)
                else:
                    self._llm = services.get_service(f"@/llm/{self._llm_provider}")  # use the model defined in config
            except Exception:
                print(f"Error initializing LLM provider '{self._llm_provider}'.")
        return self._llm

    async def add(self, input: str | KnwlInput) -> KnwlGraph:
        """
        Add input to be processed by Knwl, i.e. ingest the given text or KnwlInput object.
        """
        if isinstance(input, str):
            input = KnwlInput(text=input)
        return await self.grag.ingest(input)

    async def ingest(self, input: str | KnwlInput) -> KnwlGraph:
        """
        This is an alias for `add()`.
        """
        return await self.add(input)

    async def augment(self, question: str | KnwlInput) -> KnwlContext | None:
        if isinstance(question, str):
            input = KnwlInput(text=question)
        elif isinstance(question, KnwlInput):
            input = question
        else:
            raise TypeError(f"Invalid input type for Knwl.ask: '{type(question)}'.")

        return await self.grag.augment(input)

    async def ask(self, question: str | KnwlInput) -> KnwlAnswer:

        if isinstance(question, str):
            input = KnwlInput(text=question)
        elif isinstance(question, KnwlInput):
            input = question
        else:
            raise TypeError(f"Invalid input type for Knwl.ask: '{type(question)}'.")
        if input.params.strategy is None:
            return await self._simple_ask(question)
        else:
            augmentation = await self.grag.augment(input)
            if augmentation is None:
                return KnwlAnswer.none()
            prompt = prompts.rag.grag_ask(question=input.text, augmentation=augmentation)
            found = await self.llm.ask(prompt)
            return found

    async def add_fact(self, name: str, content: str, id: Optional[str] = None, type: Optional[str] = "Fact", ) -> KnwlNode:
        """
        Add a single node-fact to the knowledge graph.
        This effectively merges a mini-ingestion of a single node into the graph.
        """
        node = KnwlNode(id=id, name=name, description=content, type=type, )
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

    async def connect(self, source_name: Optional[str] = None, target_name: Optional[str] = None, source_id: Optional[str] = None, target_id: Optional[str] = None, relation: Optional[str] = "Relation", ) -> KnwlEdge:
        """
        Connect two nodes in the knowledge graph with a relation.
        This is a simplified method of the `semantic_graph` API.
        """

        # the id's have precedence over names
        if source_id is not None:
            if source_name is not None:
                raise ValueError("Provide either source_id or source_name, not both.")
        else:
            if source_name is None:
                raise ValueError("Either source_id or source_name must be provided.")
            else:
                sources = await self.grag.semantic_graph.get_nodes_by_name(source_name)
                if len(sources) == 0:
                    raise ValueError(f"No nodes found with name '{source_name}'.")
                source = sources[0]
        if target_id is not None:
            if target_name is not None:
                raise ValueError("Provide either target_id or target_name, not both.")
        else:
            if target_name is None:
                raise ValueError("Either target_id or target_name must be provided.")
            else:
                targets = await self.grag.semantic_graph.get_nodes_by_name(target_name)
                if len(targets) == 0:
                    raise ValueError(f"No nodes found with name '{target_name}'.")
                target = targets[0]

        if source.id == target.id:
            raise ValueError("Cannot connect a node to itself.")
        edge = KnwlEdge(source_id=source.id, target_id=target.id, description=relation, type=relation, )
        return await self.grag.semantic_graph.embed_edge(edge)  # embed, not upsert!, this is a semantic store

    async def get_config(self, *keys):
        """
        Get a config value for the current knowledge space by keys.
        For instance, to get the graph path, use `get_config("graph", "user", "path")` or `get_config("@/graph/user/path")`.
        """
        return get_config(*keys)

    async def extraction_prompt(self, text: str, entity_types: Optional[list[str]] = None) -> str:
        """
        Get the extraction prompt for the given text and optional entity types.
        You can use this prompt to test out whether your LLM is able to extract the desired entities.
        """
        from knwl.prompts.prompts import prompts

        if entity_types is not None:
            if not isinstance(entity_types, list):
                raise ValueError("entity_types must be a list of strings.")
            if not all(isinstance(et, str) for et in entity_types):
                raise ValueError("entity_types must be a list of strings.")

        return prompts.extraction.fast_graph_extraction(text, entity_types)

    async def get_node_by_id(self, node_id: str) -> KnwlNode | None:
        """
        Get a node by its Id from the knowledge graph.
        """
        return await self.grag.get_node_by_id(node_id)

    async def delete_node_by_id(self, node_id: str) -> bool:
        """
        Delete a node by its Id from the knowledge graph.
        Returns True if the node was deleted, False if it did not exist.
        """
        return await self.grag.delete_node_by_id(node_id)

    async def get_edges_between_nodes(self, source_id: str, target_id: str) -> list[KnwlEdge]:
        """
        Get all edges between two nodes by their Ids from the knowledge graph.
        """
        return await self.grag.get_edges_between_nodes(source_id, target_id)

    async def _simple_ask(self, question: str) -> KnwlAnswer:
        """
        Simple LLM QA without knowledge graph.
        This uses the default LLM service configured.
        """
        found = await self.llm.ask(question)
        return found or KnwlAnswer.none()

    async def chunk(self, doc: str | KnwlDocument) -> list[KnwlChunk]:
        """
        Chunk a document or text into smaller chunks using the configured chunker.
        Note: this method does not store the chunks, it only returns them.
        """
        if isinstance(doc, str):
            doc = KnwlDocument(content=doc)
        return await self.grag.chunk(doc)

    def get_prompt(self, prompt_type: PromptType) -> object:
        """
        Get a prompt template by its type.

        Note:
            - this is a synchronous method, unlike most of Knwl's API.
            - the MCP service (in the knwpl_api package) exposes this via its `/prompts/{prompt_type}` endpoint.

        example:
            >>> knwl = Knwl()
            >>> extraction_prompts = knwl.get_prompt(PromptType.EXTRACTION)
            >>> prompt = extraction_prompts.fast_graph_extraction("Some text to extract from.", entity_types=["Person", "Organization"])
            >>> print(prompt)
        """
        if prompt_type == PromptType.EXTRACTION:
            return prompts.extraction
        elif prompt_type == PromptType.SUMMARIZATION:
            return prompts.summarization
        elif prompt_type == PromptType.RAG:
            return prompts.rag
        elif prompt_type == PromptType.CONSTANTS:
            return prompts.constants
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

    def __repr__(self) -> str:
        from importlib.metadata import version

        knwl_version = version("knwl")
        return f"Knwl v{knwl_version} - Knwl instance (namespace={self._namespace})"

    def __str__(self) -> str:
        return self.__repr__()

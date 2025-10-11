from typing import Union
from knwl.logging import log
from knwl.models import KnwlNode, KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.services import Services
from knwl.storage import NetworkXGraphStorage, ChromaStorage
from knwl.storage.graph_base import GraphBase
from knwl.storage.vector_storage_base import VectorStorageBase
from knwl.summarization.ollama import OllamaSummarization
from knwl.summarization.summarization_base import SummarizationBase


class SemanticGraph(SemanticGraphBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)

        if (
            len(args) == 1
            and isinstance(args[0], str)
            and args[0].strip().lower() in ["memory", "test"]
        ):
            self.graph_store = NetworkXGraphStorage("memory")
            self.node_embeddings = ChromaStorage("memory")
            self.edge_embeddings = ChromaStorage("memory")
            self.summarization = OllamaSummarization()
            log(f"Semantic graph initialized all memory.")
        else:

            specs = Services.get_service_specs("semantic", override=config)
            if specs is None:
                log.error("No semantic graph service configured.")
                raise ValueError("No semantic graph service configured.")
            self.validate_config(specs)
            self.graph_store: GraphBase = self.get_service(
                specs["graph"]["graph-store"], override=config
            )
            self.node_embeddings: VectorStorageBase = self.get_service(
                specs["graph"]["node_embeddings"], override=config
            )  # print(type(self.graph_store).__name__)
            self.edge_embeddings: VectorStorageBase = self.get_service(
                specs["graph"]["edge-embeddings"], override=config
            )
            self.summarization: SummarizationBase = self.get_service(
                specs["graph"]["summarization"], override=config
            )
            log(
                f"Semantic graph initialized with {type(self.graph_store).__name__}, {type(self.node_embeddings).__name__}, {type(self.edge_embeddings).__name__}, {type(self.summarization).__name__}"
            )

    def validate_config(self, specs):
        """
        Validates the semantic graph configuration specifications.

        This method ensures that all required configuration sections are present
        in the semantic service specifications for proper graph functionality.

        Args:
            specs (dict): Configuration specifications dictionary containing
                         semantic service settings.

        Raises:
            ValueError: If any required configuration section is missing:
                       - "graph": Main graph configuration section
                       - "graph-store": Graph storage configuration
                       - "node_embeddings": Node embedding configuration
                       - "edge-embeddings": Edge embedding configuration
                       - "summarization": Summarization configuration

        Returns:
            None: Method only validates configuration and raises exceptions
                  if validation fails.
        """
        if "graph" not in specs:
            raise ValueError("No graph configuration found in semantic service.")
        if "graph-store" not in specs["graph"]:
            raise ValueError("No graph-store configured in semantic service.")
        if "node_embeddings" not in specs["graph"]:
            raise ValueError("No node_embeddings configured in semantic service.")
        if "edge-embeddings" not in specs["graph"]:
            raise ValueError("No edge-embeddings configured in semantic service.")
        if "summarization" not in specs["graph"]:
            raise ValueError("No summarization configured in semantic service.")

    async def embed_edge(self, edge: KnwlEdge) -> KnwlEdge | None:
        # TODO: consider embedding of the description only
        # this uses the automatic embedding of the edge, via Chroma by default
        if edge is None:
            return

        try:
            if edge.id is None:
                log.error("Edge must have an ID to be embedded.")
                raise ValueError("Edge must have an Id to be embedded.")
            if edge.source_id is None or edge.target_id is None:
                log.error("Edge must have both source and target IDs to be embedded.")
                raise ValueError(
                    "Edge must have both source and target IDs to be embedded."
                )  # check endpoints exist
            if not await self.node_exists(edge.source_id):
                raise ValueError(
                    f"Source node {edge.source_id} does not exist in the graph."
                )
            if not await self.node_exists(edge.target_id):
                raise ValueError(
                    f"Target node {edge.target_id} does not exist in the graph."
                )
            # merge descriptions if edge already exists
            merge_edge = await self.merge_edge_descriptions(edge)
            # add to graph store
            await self.graph_store.upsert_edge(
                edge.source_id, edge.target_id, merge_edge
            )
            # add to embedding store
            await self.edge_embeddings.upsert(
                {edge.id: merge_edge.model_dump(mode="json")}
            )
            return merge_edge
        except Exception as e:
            log(e)
            raise e

    async def embed_edges(self, edges: list[KnwlEdge]):
        if edges is None or len(edges) == 0:
            return
        for e in edges:
            await self.embed_edge(e)

    async def embed_node(self, node: KnwlNode) -> KnwlNode | None:
        if node is None:
            return None
        node = await self.merge_node_descriptions(node)
        # add to graph store
        await self.graph_store.upsert_node(node)
        # add to embedding store
        await self.node_embeddings.upsert({node.id: node.model_dump(mode="json")})
        return node

    async def merge_node_descriptions(self, node: KnwlNode) -> KnwlNode:
        """
        Merges the description of a given node with the existing description in the graph store, if
        the node already exists. The merging is done by summarizing both descriptions using the
        configured summarization service.

        This method does not upsert the node, only merges the descriptions if necessary.
        """
        # if the node exists, we summarize the existing description with the new one
        if await self.node_exists(node):
            existing_node = await self.get_node_by_id(node.id)
            if (
                existing_node is not None
                and existing_node.description is not None
                and node.description is not None
            ):
                # summarize the two descriptions
                summary = await self.summarization.summarize(
                    [existing_node.description, node.description]
                )
                if summary is not None and len(summary.strip()) > 0:
                    node = node.update(description=summary.strip())
        return node

    async def merge_edge_descriptions(self, edge: KnwlEdge) -> KnwlEdge:
        """
        Merges the description of a given edge with existing edges in the graph store that have the
        same source, target, and type. The merging is done by summarizing all descriptions using the
        configured summarization service.

        This method does not upsert the edge, only merges the descriptions if necessary.
        """
        # endpoints and type define the edge
        edges = await self.get_edges(edge.source_id, edge.target_id, edge.type)
        if edges and len(edges) > 0:
            edges.append(edge)
            # summarize the existing descriptions with the new one
            combined_description = await self.summarization.summarize(
                [e.description for e in edges if e.description]
            )
            if combined_description:
                # note that the id of the original edge is kept
                edge = edge.update(description=combined_description.strip())
        return edge

    async def embed_nodes(self, nodes: list[KnwlNode]) -> list[KnwlNode]:
        if nodes is None or len(nodes) == 0:
            return []
        coll = []
        data = {}
        for node in nodes:
            if node is None:
                continue
            node = await self.merge_node_descriptions(node)
            data[node.id] = node.model_dump(mode="json")
            n = await self.graph_store.upsert_node(node)
            coll.append(n)

        # embedding of the nodes
        await self.node_embeddings.upsert(data)
        return [KnwlNode(**d) for d in coll]

    async def get_node_by_id(self, id: str) -> KnwlNode | None:
        if id is None or len(id.strip()) == 0:
            return None
        data = await self.graph_store.get_node_by_id(id)
        if data is None:
            return None
        return KnwlNode(**data)

    async def get_edge_by_id(self, id: str) -> KnwlEdge | None:
        if id is None or len(id.strip()) == 0:
            return None
        data = await self.graph_store.get_edge_by_id(id)
        if data is None:
            return None
        return KnwlEdge(**data)

    async def node_exists(self, id: KnwlNode | str) -> bool:
        if isinstance(id, KnwlNode):
            id = id.id
        if id is None or len(id.strip()) == 0:
            return False
        return await self.graph_store.node_exists(id)

    async def get_edges(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ) -> Union[list[KnwlEdge], None]:
        found = await self.graph_store.get_edges(
            source_node_id_or_key, target_node_id, type
        )
        if found is None or len(found) == 0:
            return None
        edges = []
        for e in found:
            edges.append(KnwlEdge(**e))
        return edges

    async def merge_graph(self, graph: KnwlGraph):
        pass

    async def get_similar_nodes(self, node: KnwlNode, top_k: int = 5) -> list[KnwlNode]:
        """
        Retrieve nodes that are semantically similar to the given node.

        This method uses the node embeddings to find nodes that are most similar
        to the provided node based on their semantic content. The similarity is
        determined by querying the embedding space with the JSON representation
        of the input node.

        Args:
            node (KnwlNode): The reference node to find similar nodes for. Must have
                a valid id attribute.
            top_k (int, optional): The maximum number of similar nodes to return.
                Defaults to 5.

        Returns:
            list[KnwlNode]: A list of nodes that are most similar to the input node,
                ordered by similarity score (most similar first). Returns an empty
                list if the input node is None or has no id.
        """
        if node is None or node.id is None:
            return []
        results = await self.node_embeddings.query(node.model_dump_json(), top_k=top_k)
        nodes = []
        for r in results:
            nodes.append(KnwlNode(**r))
        return nodes

    async def get_similar_edges(self, edge: KnwlEdge, top_k: int = 5) -> list[KnwlEdge]:
        if edge is None or edge.id is None:
            return []
        results = await self.edge_embeddings.query(edge.model_dump_json(), top_k=top_k)
        # at this point you have to decide whether the graph or the vector db is considered for the actual data
        # if the vector db only contains embeddings, then you have to get the actual data from the graph store
        # for now we assume the vector db contains the actual data as well,
        edges = []
        for r in results:
            edges.append(KnwlEdge(**r))
        return edges

    async def node_count(self) -> int:
        return await self.graph_store.node_count()

    async def edge_count(self) -> int:
        return await self.graph_store.edge_count()

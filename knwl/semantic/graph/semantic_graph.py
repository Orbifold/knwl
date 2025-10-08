from knwl.logging import log
from knwl.models import KnwlNode, KnwlEdge
from knwl.models.KnwlGraph import KnwlGraph
from knwl.semantic.graph.semantic_graph_base import SemanticGraphBase
from knwl.services import Services


class SemanticGraph(SemanticGraphBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        specs = Services.get_service_specs("semantic", override=config)
        if specs is None:
            log.error("No semantic graph service configured.")
            raise ValueError("No semantic graph service configured.")
        self.validate_config(specs)
        self.graph_store = self.get_service(specs["graph"]["graph-store"], override=config)
        self.node_embeddings = self.get_service(specs["graph"]["node-embeddings"], override=config)  # print(type(self.graph_store).__name__)
        self.edge_embeddings = self.get_service(specs["graph"]["edge-embeddings"], override=config)
        self.summarization = self.get_service(specs["graph"]["summarization"], override=config)
        log(f"Semantic graph initialized with {type(self.graph_store).__name__}, {type(self.node_embeddings).__name__}, {type(self.edge_embeddings).__name__}, {type(self.summarization).__name__}")

    def validate_config(self, specs):
        if "graph" not in specs:
            raise ValueError("No graph configuration found in semantic service.")
        if "graph-store" not in specs["graph"]:
            raise ValueError("No graph-store configured in semantic service.")
        if "node-embeddings" not in specs["graph"]:
            raise ValueError("No node-embeddings configured in semantic service.")
        if "edge-embeddings" not in specs["graph"]:
            raise ValueError("No edge-embeddings configured in semantic service.")
        if "summarization" not in specs["graph"]:
            raise ValueError("No summarization configured in semantic service.")

    async def embed_edge(self, edge: KnwlEdge):
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
                raise ValueError("Edge must have both source and target IDs to be embedded.")  # check endpoints exist
            if not await self.node_exists(edge.source_id):
                raise ValueError(f"Source node {edge.source_id} does not exist in the graph.")
            if not await self.node_exists(edge.target_id):
                raise ValueError(f"Target node {edge.target_id} does not exist in the graph.")

            await self.edge_embeddings.upsert({edge.id: edge.model_dump(mode="json")})
        except Exception as e:
            log(e)
            raise e

    async def embed_edges(self, edges: list[KnwlEdge]):
        if edges is None or len(edges) == 0:
            return
        for e in edges:
            await self.embed_edge(e)

    async def embed_node(self, node: KnwlNode):
        if node is None:
            return
        if node.id is None:
            log.error("Node must have an ID to be embedded.")
            raise ValueError("Node must have an Id to be embedded.")
        await self.node_embeddings.upsert({node.id: node.model_dump(mode="json")})

    async def embed_nodes(self, nodes: list[KnwlNode]):
        if nodes is None or len(nodes) == 0:
            return
        data = {}
        for node in nodes:
            if node is None:
                continue
            if node.id is None:
                log.error("Node must have an ID to be embedded.")
                raise ValueError("Node must have an Id to be embedded.")
            data[node.id] = node.model_dump(mode="json")
        await self.node_embeddings.upsert(data)

    async def get_node_by_id(self, id: str) -> KnwlNode | None:
        if id is None or len(id.strip()) == 0:
            return None
        data = await self.node_embeddings.get_by_id(id)
        if data is None:
            return None
        return KnwlNode(**data)

    async def get_edge_by_id(self, id: str) -> KnwlEdge | None:
        if id is None or len(id.strip()) == 0:
            return None
        data = await self.edge_embeddings.get_by_id(id)
        if data is None:
            return None
        return KnwlEdge(**data)

    async def node_exists(self, id: KnwlNode | str) -> bool:
        if isinstance(id, KnwlNode):
            id = id.id
        if id is None or len(id.strip()) == 0:
            return False
        return await self.graph_store.node_exists(id)

    async def get_edge(self, source_id: str, target_id: str, label: str) -> KnwlEdge | None:
        return await self.graph_store.get_edge(source_id, target_id, label)

    async def merge_graph(self, graph: KnwlGraph):
        pass

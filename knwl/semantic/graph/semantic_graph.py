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

    async def embed_edge(self, sedge: KnwlEdge):
        pass

    async def merge_graph(self, graph: KnwlGraph):
        pass

    async def embed_node(self, node: KnwlNode):
        pass

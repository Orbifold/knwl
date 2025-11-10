from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlEdge
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlGraph import KnwlGraph
from knwl.models.KnwlNode import KnwlNode
from knwl.prompts import prompts


class GraphExtractionBase(FrameworkBase, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
    @abstractmethod
    async def extract(
        self, text: str, entities: list[str] = None, chunk_id: str = None
    ) -> KnwlExtraction | None:
        pass

    @abstractmethod
    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        pass

    @abstractmethod
    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        pass

    @abstractmethod
    async def extract_graph(
        self, text: str, entities: list[str] = None, chunk_id: str = None
    ) -> KnwlGraph | None:
        pass

    @staticmethod
    def records_to_json(records: list[list]) -> dict:
        result = {
            "entities": [],
            "relationships": [],
            "keywords": [],
        }
        for rec in records:
            if rec[0] == "entity":
                try:
                    result["entities"].append(
                        {
                            "name": rec[1],
                            "type": rec[2],
                            "description": rec[3],
                        }
                    )
                except Exception as e:
                    from knwl.logging import log
                    log.error(f"Error parsing entity record: {rec}: \n{e}")
            elif rec[0] == "relationship":
                try:
                    result["relationships"].append(
                        {
                            "source": rec[1],
                            "target": rec[2],
                            "description": rec[3],
                            "types": (
                                [u.strip() for u in rec[4].split(",")]
                                if rec[4] is not None
                                else []
                            ),
                            "weight": float(rec[5]) if len(rec) > 5 and rec[5] else 1.0,
                        }
                    )
                except Exception as e:
                    from knwl.logging import log
                    log.error(f"Error parsing relationship record: {rec}: \n{e}")
            elif rec[0] == "content_keywords":
                result["keywords"].extend(rec[1].split(", "))
        #  make keywords unique
        result["keywords"] = list(set(result["keywords"]))
        return result

    @staticmethod
    def records_to_extraction(
        records: list[list], chunk_id: str = None
    ) -> KnwlExtraction:
        dic = GraphExtractionBase.records_to_json(records)
        if len(dic["entities"]) == 0:
            return KnwlExtraction(nodes={}, edges={}, keywords=[])
        nodes: dict[str, list[KnwlNode]] = {}
        edges: dict[str, list[KnwlEdge]] = {}

        node_map = {}  # map of node names to node ids
        for item in dic["entities"]:
            node = KnwlNode(
                name=item["name"],
                type=item["type"],
                description=item["description"],
                chunk_ids=[chunk_id] if chunk_id else [],
            )
            if node.name not in nodes:
                nodes[node.name] = [node]
            else:
                coll = nodes[node.name]
                found = [
                    e
                    for e in coll
                    if e.type == node.type and e.description == node.description
                ]
                if len(found) == 0:
                    coll.append(node)
            node_map[node.name] = node.id
        for item in dic["relationships"]:
            edge = KnwlEdge(
                source_id=item["source"],
                target_id=item["target"],
                description=item["description"],
                keywords=item["types"],
                weight=item["weight"],
                chunk_ids=[chunk_id] if chunk_id else [],
                type=item["types"][0] if len(item["types"]) > 0 else "Unknown",
            )
            # the edge key is the tuple of the source and target names, NOT the ids. Is corrected below
            edge_key = f"({edge.source_id},{edge.target_id})"
            if (edge.source_id, edge.target_id) not in edges:
                edges[edge_key] = [edge]
            else:
                coll = edges[edge_key]
                found = [
                    e
                    for e in coll
                    if e.description == edge.description and e.keywords == edge.keywords
                ]
                if len(found) == 0:
                    coll.append(edge)

        # the edge endpoints are the names and not the ids
        corrected_edges = {}
        for key in edges:
            for e in edges[key]:

                if e.source_id not in node_map or e.target_id not in node_map:
                    #  happens if the LLM creates edges to entities that are not in the graph
                    continue
                if key not in corrected_edges:
                    corrected_edges[key] = []
                source_id = node_map[e.source_id]
                target_id = node_map[e.target_id]
                corrected_edge = KnwlEdge(
                    source_id=source_id,
                    target_id=target_id,
                    description=e.description,
                    keywords=e.keywords,
                    weight=e.weight,
                    chunk_ids=e.chunk_ids,
                    type=e.type
                )
                corrected_edges[key].append(corrected_edge)
        return KnwlExtraction(
            nodes=nodes, edges=corrected_edges, keywords=dic["keywords"] or []
        )

    @staticmethod
    def extraction_to_graph(extraction: KnwlExtraction) -> KnwlGraph:
        nodes = []
        edges = []

        for name in extraction.nodes:
            for node in extraction.nodes[name]:
                nodes.append(node)
        for key in extraction.edges:
            for edge in extraction.edges[key]:
                edges.append(edge)
        return KnwlGraph(nodes=nodes, edges=edges, keywords=extraction.keywords or [])

    def get_extraction_prompt(self, text, entity_types=None):
        if self.extraction_mode == "fast":
            return prompts.extraction.fast_graph_extraction(text, entity_types)
        if self.extraction_mode == "full":
            return prompts.extraction.full_graph_extraction(text, entity_types)
        else:
            raise ValueError(f"Unknown extraction mode: {self.extraction_mode}")

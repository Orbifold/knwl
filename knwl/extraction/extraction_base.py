from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlEdge
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlNode import KnwlNode


class ExtractionBase(FrameworkBase, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def extract(self, text: str, entities: list[str] = None) -> KnwlExtraction | None:
        pass

    @abstractmethod
    async def extract_records(self, text: str, entities: list[str] = None) -> list[list] | None:
        pass

    @abstractmethod
    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        pass

    def records_to_json(self, records: list[list]) -> dict:
        result = {"entities": [], "relationships": [], "keywords": [], }
        for rec in records:
            if rec[0] == "entity":
                result["entities"].append({"name": rec[1], "type": rec[2], "description": rec[3], })
            elif rec[0] == "relationship":
                result["relationships"].append({"source": rec[1], "target": rec[2], "description": rec[3], "types": [u.strip() for u in rec[4].split(",")] if rec[4] is not None else [], "weight": float(rec[5]) if len(rec) > 5 and rec[5] else 1.0, })
            elif rec[0] == "content_keywords":
                result["keywords"] = rec[1].split(", ")
        return result

    def records_to_extraction(self, records: list[list]) -> KnwlExtraction:
        dic = self.records_to_json(records)

        nodes: dict[str, list[KnwlNode]] = {}
        edges: dict[str, list[KnwlEdge]] = {}

        node_map = {}  # map of node names to node ids
        for item in dic["entities"]:
            node = KnwlNode(name=item["name"], type=item["type"], description=item["description"])
            if node.name not in nodes:
                nodes[node.name] = [node]
            else:
                coll = nodes[node.name]
                found = [e for e in coll if e.type == node.type and e.description == node.description]
                if len(found) == 0:
                    coll.append(node)
            node_map[node.name] = node.id
        for item in dic["relationships"]:
            edge = KnwlEdge(sourceId=item["source"], targetId=item["target"], description=item["description"], keywords=item["types"], weight=item["weight"])
            # the edge key is the tuple of the source and target names, NOT the ids. Is corrected below
            edge_key = f"({edge.sourceId},{edge.targetId})"
            if (edge.sourceId, edge.targetId) not in edges:
                edges[edge_key] = [edge]
            else:
                coll = edges[edge_key]
                found = [e for e in coll if e.description == edge.description and e.keywords == edge.keywords]
                if len(found) == 0:
                    coll.append(edge)

        # the edge endpoints are the names and not the ids
        corrected_edges = {}
        for key in edges:
            for e in edges[key]:

                if e.sourceId not in node_map or e.targetId not in node_map:
                    #  happens if the LLM creates edges to entities that are not in the graph
                    continue
                if key not in corrected_edges:
                    corrected_edges[key] = []
                source_id = node_map[e.sourceId]
                target_id = node_map[e.targetId]
                corrected_edge = KnwlEdge(sourceId=source_id, targetId=target_id, description=e.description, keywords=e.keywords, weight=e.weight, chunkIds=e.chunkIds, )
                corrected_edges[key].append(corrected_edge)
        return KnwlExtraction(nodes=nodes, edges=corrected_edges, keywords=dic["keywords"] or [])

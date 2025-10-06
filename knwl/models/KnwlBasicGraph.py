from knwl.models.KnwlBasicNode import KnwlBasicNode
from knwl.models.KnwlBasicEdge import KnwlBasicEdge


import networkx as nx


from dataclasses import dataclass, field
from typing import List
from uuid import uuid4


@dataclass
class KnwlBasicGraph:
    """
    This is in essence a JSON graph structure.
    """
    nodes: List[KnwlBasicNode]
    edges: List[KnwlBasicEdge]
    id: str = field(default=str(uuid4()))
    typeName: str = "KnwlBasicGraph"

    def is_consistent(self) -> bool:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_ids = self.get_node_ids()

        for edge in self.edges:
            if edge.sourceId not in node_ids:
                logger.error(f"Source node {edge.sourceId} of edge {edge.id} is not in the node list.")
                return False
            if edge.targetId not in node_ids:
                logger.error(f"Target node {edge.targetId} of edge {edge.id} is not in the node list.")
                return False
        return True

    def get_node_ids(self) -> List[str]:
        return [node.id for node in self.nodes]

    def get_edge_ids(self) -> List[str]:
        return [edge.id for edge in self.edges]

    def __post_init__(self):
        if not self.is_consistent():
            raise ValueError("The graph is not consistent.")

    def to_nx_graph(self):
        G = nx.Graph()
        for node in self.nodes:
            G.add_node(node.id, name=node.name, type=node.type, description=node.description)
        for edge in self.edges:
            G.add_edge(edge.sourceId, edge.targetId, description=edge.description)
        return G

    def write_graphml(self, file_name):
        G = self.to_nx_graph()
        nx.write_graphml(G, file_name)

    @staticmethod
    def from_json_graph(json_graph):

        nodes = [KnwlBasicNode(**node) for node in json_graph["nodes"]]
        edges = [KnwlBasicEdge(**edge) for edge in json_graph["edges"]]
        return KnwlBasicGraph(nodes=nodes, edges=edges)

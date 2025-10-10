from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.utils import get_endpoint_ids


class KnwlExtraction(BaseModel):
    """
        A class used to represent a Knowledge Extraction.
        Note that the id's of the nodes and edges are semantic, ie. actual names.
        The conversion to real identifiers happens downstream when this is merged into the knowledge graph.

        Attributes
        ----------
        nodes : dict[str, List[KnwlNode]]
            A dictionary where the keys are names of entities and the values are lists of KnwlNode objects. These can have different types and descriptions.
        edges : dict[str, List[KnwlEdge]]
            A dictionary where the keys are strings and the values are lists of KnwlEdge objects.
            Note that the key is the tuple of endpoints sorted in ascending order.
            The KG is undirected and the key is used to ensure that the same edge is not added twice.
        typeName : str
            A string representing the type name of the extraction, default is "KnwlExtraction".
        id : str
            A unique identifier for the extraction, default is a new UUID4 string.

        example:

        `
        {
      "nodes": {
        "Barack Obama": [
          {
            "name": "Barack Obama",
            "type": "person",
            "typeName": "KnwlNode",
            "id": "node-3fcbf8e8e1c4f474f9d215fbd4f24a03",
            "description": "Barack Obama is a person who was elected president.",
            "chunkIds": []
          }
        ],
        "Hawaii": [
          {
            "name": "Hawaii",
            "type": "geo",
            "typeName": "KnwlNode",
            "id": "node-54c7d58158ebdb15e6f73c7cec50656f",
            "description": "Hawaii is a geographical location where Barack Obama was born.",
            "chunkIds": []
          }
        ],
        "2008": [
          {
            "name": "2008",
            "type": "event",
            "typeName": "KnwlNode",
            "id": "node-36b33d2175de7f6b924fcbd5b11c930b",
            "description": "2008 refers to the year Barack Obama was elected president.",
            "chunkIds": []
          }
        ]
      },
      "edges": {
        "(Barack Obama,2008)": [
          {
            "sourceId": "node-3fcbf8e8e1c4f474f9d215fbd4f24a03",
            "target_id": "node-36b33d2175de7f6b924fcbd5b11c930b",
            "typeName": "KnwlEdge",
            "id": "edge-058b135b093daa9960f346109bd0c151",
            "chunkIds": [],
            "keywords": [
              "election",
              " timeline"
            ],
            "description": "Barack Obama was elected in 2008.",
            "weight": 7.0
          }
        ],
        "(Barack Obama,Hawaii)": [
          {
            "sourceId": "node-3fcbf8e8e1c4f474f9d215fbd4f24a03",
            "target_id": "node-54c7d58158ebdb15e6f73c7cec50656f",
            "typeName": "KnwlEdge",
            "id": "edge-47ec3d753a51682ceeb9dc7057cf7be5",
            "chunkIds": [],
            "keywords": [
              "birthplace",
              " location"
            ],
            "description": "Barack Obama was born in Hawaii.",
            "weight": 6.0
          }
        ]
      },
      "keywords": [
        "election",
        "birthplace",
        "location",
        "timeline"
      ],
      "typeName": "KnwlExtraction",
      "id": "53a45fed-04f2-455d-9746-8be9d25f6c3f"
    }
        `

    """

    nodes: dict[str, List[KnwlNode]]
    edges: dict[str, List[KnwlEdge]]
    keywords: List[str] = Field(default_factory=list)
    typeName: str = "KnwlExtraction"
    id: str = Field(default_factory=lambda: str(uuid4()))

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate that the graph is consistent after initialization."""
        if not self.is_consistent():
            print("Warning: the extracted graph is not consistent, fixing this.")
            self.make_consistent()
        return self

    def is_consistent(self) -> bool:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_keys = self.get_node_keys()
        edge_keys = self.get_edge_keys()

        for edge in self.edges:
            source_id, target_id = get_endpoint_ids(edge)
            if source_id is None or target_id is None:
                return False
            if source_id not in node_keys or target_id not in node_keys:
                return False
        return True

    def make_consistent(self):
        """
        Make the graph consistent: remove edges with endpoints that are not in the node list.
        """
        node_keys = self.get_node_keys()
        edge_keys = self.get_edge_keys()
        new_edges = {}
        for edge in self.edges:
            source_id, target_id = get_endpoint_ids(edge)
            if source_id is not None and target_id is not None:
                if source_id in node_keys and target_id in node_keys:
                    new_edges[edge] = self.edges[edge]
        self.edges = new_edges

    def get_node_ids(self) -> List[str]:
        coll = []
        for k in self.nodes.keys():
            for n in self.nodes[k]:
                coll.append(n.id)
        return coll

    def get_edge_ids(self) -> List[str]:
        coll = []
        for k in self.edges.keys():
            for e in self.edges[k]:
                coll.append(e.id)
        return coll

    def get_node_keys(self) -> List[str]:
        return list(self.nodes.keys())

    def get_edge_keys(self) -> List[str]:
        return list(self.edges.keys())

    def get_all_node_types(self) -> List[str]:
        types = set()
        for k in self.nodes.keys():
            for n in self.nodes[k]:
                types.add(n.type)
        return list(types)

    def get_all_edge_types(self) -> List[str]:
        types = set()
        for k in self.edges.keys():
            for e in self.edges[k]:
                for t in e.keywords:
                    types.add(t)
        return list(types)

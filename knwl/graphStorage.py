import shutil
from dataclasses import asdict
from typing import cast, Dict, Any, Tuple

import networkx as nx

from knwl.settings import settings
from knwl.utils import *


class GraphStorage(StorageNameSpace):
    """
    A class to handle storage and manipulation of an undirected graph using NetworkX.
        - the id of nodes and edges is a uuid4 string but one could also use the combination name+type as a primary key.
        - the graph is stringly type with in/out based on KnwlNode and KnwlEdge dataclasses, the underlying storage is however based on a dictionary. In this sense, this is a semantic layer (business data rather than storage data) above the actual graph storage.

    Methods
    -------
    load(file_name: str) -> nx.Graph | None
        Static method to load a graph from a GraphML file.

    write(graph: nx.Graph, file_name: str)
        Static method to write a graph to a GraphML file.

    __post_init__()
        Initializes the GraphStorage instance, loading a pre-existing graph if available.

    async save()
        Asynchronously saves the current graph to a file.

    async node_exists(node_id: str) -> bool
        Checks if a node exists in the graph.

    async edge_exists(source_or_key: str, target_node_id: str) -> bool
        Checks if an edge exists between two nodes in the graph.

    async get_node_by_id(node_id: str) -> Union[dict, None]
        Retrieves the attributes of a node.

    async node_degree(node_id: str) -> int
        Returns the degree of a node.

    async edge_degree(source_id: str, target_id: str) -> int
        Returns the combined degree of two nodes.

    async get_edge(source_or_key: str, target_node_id: str) -> Union[dict, None]
        Retrieves the attributes of an edge.

    async get_node_edges(source_or_key: str)
        Retrieves all edges connected to a node.

    async upsert_node(node_id: str, node_data: object)
        Inserts or updates a node with the given data.

    async upsert_edge(source_or_key: str, target_node_id: str, edge_data: object)
        Inserts or updates an edge with the given data.

    async clear()
        Clears the graph and removes the associated file.

    async node_count() -> int
        Returns the number of nodes in the graph.

    async edge_count() -> int
        Returns the number of edges in the graph.

    async remove_node(node_id: str)
        Removes a node from the graph.

    async remove_edge(source_or_key: str, target_node_id: str)
        Removes an edge from the graph.

    async get_nodes() -> list
        Returns a list of all nodes in the graph.

    async get_edges() -> list
        Returns a list of all edges in the graph.

    async get_edge_weight(source_or_key: str, target_node_id: str) -> Union[float, None]
        Retrieves the weight of an edge if it exists.
    """
    graph: nx.Graph

    file_path: str | None
    parent_path: str | None

    def __init__(self, namespace: str = "default", caching: bool = False):
        super().__init__(namespace, caching)
        if self.caching:
            self.file_path = os.path.join(settings.working_dir, f"graphdb_{self.namespace}", f"data.graphml")
            self.parent_path = os.path.dirname(self.file_path)
            os.makedirs(self.parent_path, exist_ok=True)
            preloaded_graph = GraphStorage.load(self.file_path)
            if preloaded_graph is not None:
                logger.info(f"Loaded graph from {self.file_path} with {preloaded_graph.number_of_nodes()} nodes, {preloaded_graph.number_of_edges()} edges")
                # remove the label attributes if present
                for node in preloaded_graph.nodes:
                    if "label" in preloaded_graph.nodes[node]:
                        del preloaded_graph.nodes[node]["label"]
                for edge in preloaded_graph.edges:
                    if "label" in preloaded_graph.edges[edge]:
                        del preloaded_graph.edges[edge]["label"]
            self.graph = preloaded_graph or nx.Graph()
        else:
            self.graph = nx.Graph()
            self.file_path = None
            self.parent_path = None

    @staticmethod
    def to_knwl_node(node: dict) -> KnwlNode | None:
        if node is None:
            return None
        if "label" in node:
            del node["label"]
        return KnwlNode(**node)

    @staticmethod
    def to_knwl_edge(edge: dict) -> KnwlEdge | None:
        if edge is None:
            return None
        # the label is added for visualization of GraphML
        if "label" in edge:
            del edge["label"]
        return KnwlEdge(**edge)

    @staticmethod
    def from_knwl_node(node: KnwlNode) -> dict | None:
        if node is None:
            return None
        return asdict(node)

    @staticmethod
    def from_knwl_edge(edge: KnwlEdge) -> dict | None:
        if edge is None:
            return None
        return asdict(edge)

    @staticmethod
    def load(file_name) -> nx.Graph | None:
        if os.path.exists(file_name):
            return nx.read_graphml(file_name)
        return None

    @staticmethod
    def write(graph: nx.Graph, file_name):
        logger.info(f"Writing graph with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        # the label is the id, helps with visualization
        nx.set_node_attributes(graph, {id: str(id) for id in graph.nodes}, "label")
        nx.write_graphml(graph, file_name)

    async def save(self):
        if self.caching:
            GraphStorage.write(self.graph, self.file_path)

    async def node_exists(self, node_id: str) -> bool:
        if str.strip(node_id) == "":
            return False
        return self.graph.has_node(node_id)

    async def edge_exists(self, source_or_key: str, target_node_id: str = None) -> bool:
        source_id = None
        target_id = None
        if target_node_id is None:
            if isinstance(source_or_key, KnwlEdge):
                source_id = source_or_key.sourceId
                target_id = source_or_key.targetId

            if isinstance(source_or_key, tuple):
                source_id = source_or_key[0]
                target_id = source_or_key[1]

            if isinstance(source_or_key, str):
                match = re.match(r"\((.*?),(.*?)\)", source_or_key)
                if match:
                    source_id, target_id = match.groups()
                    source_id = str.strip(source_id)
                    target_id = str.strip(target_id)
                else:
                    raise ValueError(f"Invalid edge_id format: {source_or_key}")
        else:
            if isinstance(source_or_key, KnwlNode):
                source_id = source_or_key.id
            elif isinstance(source_or_key, dict):
                source_id = source_or_key.get("sourceId", None)
            else:
                source_id = source_or_key
            if isinstance(target_node_id, KnwlNode):
                target_id = target_node_id.id
            elif isinstance(target_node_id, dict):
                target_id = target_node_id.get("targetId", None)
            else:
                target_id = target_node_id
        if source_id is None or target_id is None:
            raise ValueError("Insufficient data to check edge existence")
        return self.graph.has_edge(source_id, target_id)

    async def get_node_by_id(self, node_id: str) -> Union[KnwlNode, None]:
        found = self.graph.nodes.get(node_id)
        if found:
            found["id"] = node_id
            return GraphStorage.to_knwl_node(found)

    async def get_node_by_name(self, node_name: str) -> Union[List[KnwlNode], None]:
        found = []
        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            if node.get("name", None) == node_name:
                node["id"] = node_id
                found.append(GraphStorage.to_knwl_node(node))
        return found

    async def node_degree(self, node_id: str) -> int:
        return self.graph.degree(node_id)

    async def edge_degree(self, source_id: str, target_id: str) -> int:
        return self.graph.degree(source_id) + self.graph.degree(target_id)

    async def get_edge(self, source_node_id: str, target_node_id: str = None) -> Union[KnwlEdge, None]:
        if target_node_id is None:
            match = re.match(r"\((.*?),(.*?)\)", source_node_id)
            if match:
                source_id, target_id = match.groups()
                source_id = str.strip(source_id)
                target_id = str.strip(target_id)
            else:
                raise ValueError(f"Invalid edge_id format: {source_node_id}")
            found = self.graph.edges.get((source_id, target_id))
        found = self.graph.edges.get((source_node_id, target_node_id))
        if found:
            found["sourceId"] = source_node_id
            found["targetId"] = target_node_id
            return GraphStorage.to_knwl_edge(found)
        else:
            return None

    async def get_node_edges(self, source_node_id: str) -> List[KnwlEdge] | None:
        """
        Retrieves all edges connected to the given node.

        Args:
            source_node_id (str): The ID of the source node.

        Returns:
            List[KnwlEdge] | None: A list of KnwlEdge objects if the node exists, None otherwise.
        """
        if self.node_exists(source_node_id):
            tuples = list(self.graph.edges(source_node_id))

            raw = [{"sourceId": t[0], "targetId": t[1], **self.graph.get_edge_data(t[0], t[1], {})} for t in tuples]
            return [GraphStorage.to_knwl_edge(edge) for edge in raw]
        return None

    async def get_attached_edges(self, nodes: List[KnwlNode]) -> List[KnwlEdge]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (List[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            List[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])
        edges = []
        for n in nodes:
            n_edges = await self.get_node_edges(n.id)
            # ensure the list is unique based on the id of KnwlEdge
            edges.extend([e for e in n_edges if e is not None and e.id not in [ee.id for ee in edges]])
        return edges

    async def get_edge_degrees(self, edges: List[KnwlEdge]) -> List[int]:
        """
        Asynchronously retrieves the degrees of the given edges.

        Args:
            edges (List[KnwlEdge]): A list of KnwlEdge objects for which to retrieve degrees.

        Returns:
            List[int]: A list of degrees for the given edges.
        """
        return await asyncio.gather(*[self.edge_degree(e.sourceId, e.targetId) for e in edges])

    async def get_semantic_endpoints(self, edge_ids: List[str]) -> dict[str, tuple[str, str]]:
        """
        Asynchronously retrieves the names of the nodes with the given IDs.

        Args:
            edge_ids (List[str]): A list of node IDs for which to retrieve names.

        Returns:
            List[str]: A list of node names.
        """
        edges = await asyncio.gather(*[self.get_edge_by_id(id) for id in edge_ids])
        coll = {}
        for e in edges:
            source_id = e.sourceId
            target_id = e.targetId
            source_node = await self.get_node_by_id(source_id)
            target_node = await self.get_node_by_id(target_id)
            if source_node and target_node:
                coll[e.id] = (source_node.name, target_node.name)
        return coll

    async def get_edge_by_id(self, edge_id: str) -> KnwlEdge | None:
        for edge in self.graph.edges(data=True):
            if edge[2]["id"] == edge_id:
                found = edge[2]
                found["id"] = edge_id
                found = GraphStorage.to_knwl_edge(found)
                return found
        raise ValueError(f"Edge with id {edge_id} not found")

    async def upsert_node(self, node_id: object, node_data: object = None):
        if node_id is None:
            raise ValueError("Insufficient data to upsert node")

        if node_data is None:
            if isinstance(node_id, KnwlNode):
                node_data = asdict(node_id)
                node_id = node_data.get("id", node_id)
            else:
                node_data = cast(dict, node_id)
                node_id = node_data.get("id", str(uuid4()))
        else:
            if not isinstance(node_id, str):
                raise ValueError("Node Id must be a string")
            if str.strip(node_id) == "":
                raise ValueError("Node Id must not be empty")
            if isinstance(node_data, KnwlNode):
                node_data = asdict(node_data)
            else:
                node_data = cast(dict, node_data)
        node_data["id"] = node_id

        self.graph.add_node(node_id, **node_data)

    async def upsert_edge(self, source_node_id: str, target_node_id: str = None, edge_data: object = None):
        if isinstance(source_node_id, KnwlEdge):
            edge_data = asdict(source_node_id)
            source_node_id = edge_data.get("sourceId", None)
            target_node_id = edge_data.get("targetId", None)
        if isinstance(source_node_id, tuple):
            source_node_id, target_node_id = source_node_id
            edge_data = cast(dict, edge_data or {})
        if isinstance(source_node_id, KnwlNode):
            source_node_id = source_node_id.id
        if isinstance(target_node_id, KnwlNode):
            target_node_id = target_node_id.id
        if isinstance(edge_data, KnwlEdge):
            source_node_id = edge_data.sourceId
            target_node_id = edge_data.targetId
            edge_data = asdict(edge_data)
        if isinstance(source_node_id, str):
            if target_node_id is None:
                raise ValueError("Insufficient data to upsert edge, missing target node id")
            edge_data = cast(dict, edge_data or {})

        if target_node_id is None:
            raise ValueError("Insufficient data to upsert edge, missing target node id")
        if source_node_id is None:
            raise ValueError("Insufficient data to upsert edge, missing source node id")
        if "id" not in edge_data:
            edge_data["id"] = str(uuid4())
        edge_data["sourceId"] = source_node_id
        edge_data["targetId"] = target_node_id
        self.graph.add_edge(source_node_id, target_node_id, **edge_data)

    async def clear(self):
        self.graph.clear()
        if self.caching:
            await self.save()

    async def node_count(self):
        return self.graph.number_of_nodes()

    async def edge_count(self):
        return self.graph.number_of_edges()

    async def remove_node(self, node_id: object):
        if isinstance(node_id, KnwlNode):
            node_id = node_id.id

        self.graph.remove_node(node_id)

    async def remove_edge(self, source_node_id: object, target_node_id: str = None):
        sourceId = None
        targetId = None
        if isinstance(source_node_id, KnwlEdge):
            sourceId = source_node_id.sourceId
            targetId = source_node_id.targetId
        if isinstance(source_node_id, tuple):
            sourceId, targetId = source_node_id
        if isinstance(source_node_id, KnwlNode):
            sourceId = source_node_id.id
        if isinstance(target_node_id, KnwlNode):
            targetId = target_node_id.id
        if isinstance(source_node_id, str):
            sourceId = source_node_id
            if target_node_id is None:
                raise ValueError("Insufficient data to remove edge, missing target node id")
            else:
                targetId = target_node_id
        self.graph.remove_edge(sourceId, targetId)

    async def get_nodes(self) -> List[KnwlNode]:
        found = list(self.graph.nodes)
        return [GraphStorage.to_knwl_node(self.graph.nodes[node_id]) for node_id in found]

    async def get_edges(self) -> List[KnwlEdge]:
        found = list(self.graph.edges)
        return [GraphStorage.to_knwl_edge(self.graph.edges[edge_id]) for edge_id in found]

    async def get_edge_weight(self, source_node_id: object, target_node_id: str = None) -> float:
        if isinstance(source_node_id, KnwlEdge):
            return source_node_id.weight
        if not self.graph.has_edge(source_node_id, target_node_id):
            raise ValueError(f"Edge {source_node_id} -> {target_node_id} does not exist")
        return self.graph.get_edge_data(source_node_id, target_node_id).get("weight", 1.0)

    async def unsave(self) -> None:
        if os.path.exists(self.file_path) and self.caching:
            shutil.rmtree(self.parent_path)

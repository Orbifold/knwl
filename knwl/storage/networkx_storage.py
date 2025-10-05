import shutil
from dataclasses import asdict
from typing import cast
from uuid import uuid4

import networkx as nx

from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.storage.graph_base import GraphBase
from knwl.utils import *
import ast


class NetworkXGraphStorage(GraphBase):
    """
    A class to handle storage and manipulation of an undirected graph using NetworkX.
        - the id of nodes and edges is a uuid4 string but one could also use the combination name+type as a primary key.
        - the graph is stringly type with in/out based on KnwlNode and KnwlEdge dataclasses, the underlying storage is however based on a dictionary. In this sense, this is a semantic layer (business data rather than storage data) above the actual graph storage.


    """
    graph: nx.Graph

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self.memory = self.get_param(["graph", "nx", "memory"], args, kwargs, default=False, override=config)
        self.path = self.get_param(["graph", "nx", "path"], args, kwargs, default="$test/vector", override=config, )
        self.format = self.get_param(["graph", "nx", "format"], args, kwargs, default="graphml", override=config)
        if not self.memory and self.path is not None:
            # self.file_path = os.path.join(config.working_dir, f"graphdb_{self.namespace}", f"data.graphml")
            self.path = get_full_path(self.path)
            if os.path.exists(self.path):
                preloaded_graph = NetworkXGraphStorage.load(self.path)
                if preloaded_graph is not None:
                    logger.info(f"Loaded graph from {self.path} with {preloaded_graph.number_of_nodes()} nodes, {preloaded_graph.number_of_edges()} edges")
                    # remove the label attributes if present
                    # todo: why is this needed?
                    for node in preloaded_graph.nodes:
                        if "label" in preloaded_graph.nodes[node]:
                            del preloaded_graph.nodes[node]["label"]
                    for edge in preloaded_graph.edges:
                        if "label" in preloaded_graph.edges[edge]:
                            del preloaded_graph.edges[edge]["label"]
                    self.graph = preloaded_graph
                else:
                    # failed to load the graph from file
                    self.graph = nx.Graph()
            else:
                self.graph = nx.Graph()
        else:
            self.graph = nx.Graph()
            self.path = None

    @staticmethod
    def to_knwl_node(node: dict) -> KnwlNode | None:
        if node is None:
            return None
        if "label" in node:
            del node["label"]
        # Convert stringified lists back to actual lists
        for key, value in node.items():
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                try:
                    # Safely evaluate the string as a list
                    node[key] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    # If evaluation fails, keep as string
                    pass
        return KnwlNode(**node)

    @staticmethod
    def to_knwl_edge(edge: dict) -> KnwlEdge | None:
        if edge is None:
            return None
        # the label is added for visualization of GraphML
        if "label" in edge:
            del edge["label"]
        # Convert stringified lists back to actual lists
        for key, value in edge.items():
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                try:
                    # Safely evaluate the string as a list
                    edge[key] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    # If evaluation fails, keep as string
                    pass
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
        try:
            if os.path.exists(file_name):
                return nx.read_graphml(file_name)
        except Exception as e:
            logger.error(f"Error loading graph from {file_name}: {e}")
            return None

    @staticmethod
    def write(graph: nx.Graph, file_name):
        logger.info(f"Writing graph with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        # the label is the id, helps with visualization
        nx.set_node_attributes(graph, {id: str(id) for id in graph.nodes}, "label")
        
        # Convert list attributes to strings and remove None values for GraphML compatibility
        for node_id, node_data in graph.nodes(data=True):
            keys_to_remove = []
            for key, value in node_data.items():
                if value is None:
                    keys_to_remove.append(key)
                elif isinstance(value, list):
                    graph.nodes[node_id][key] = str(value)
            for key in keys_to_remove:
                del graph.nodes[node_id][key]
        
        for edge in graph.edges(data=True):
            edge_data = edge[2]
            keys_to_remove = []
            for key, value in edge_data.items():
                if value is None:
                    keys_to_remove.append(key)
                elif isinstance(value, list):
                    edge_data[key] = str(value)
            for key in keys_to_remove:
                del edge_data[key]
        
        nx.write_graphml(graph, file_name)

    async def save(self):
        if not self.memory and self.path is not None:
            NetworkXGraphStorage.write(self.graph, self.path)

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
            return NetworkXGraphStorage.to_knwl_node(found)

    async def get_node_by_name(self, node_name: str) -> Union[List[KnwlNode], None]:
        found = []
        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            if node.get("name", None) == node_name:
                node["id"] = node_id
                found.append(NetworkXGraphStorage.to_knwl_node(node))
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
            return NetworkXGraphStorage.to_knwl_edge(found)
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
        if await self.node_exists(source_node_id):
            tuples = list(self.graph.edges(source_node_id))

            raw = [{"sourceId": t[0], "targetId": t[1], **self.graph.get_edge_data(t[0], t[1], {})} for t in tuples]
            return [NetworkXGraphStorage.to_knwl_edge(edge) for edge in raw]
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
                found = NetworkXGraphStorage.to_knwl_edge(found)
                return found
        raise ValueError(f"Edge with id {edge_id} not found")

    async def upsert_node(self, node_id: object, node_data: object = None):
        if node_id is None:
            raise ValueError("Insufficient data to upsert node")

        if node_data is None:
            if isinstance(node_id, KnwlNode):
                node_data = node_id.model_dump(mode="json")
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
                node_data = node_data.model_dump(mode="json")
            else:
                node_data = cast(dict, node_data)
        node_data["id"] = node_id

        self.graph.add_node(node_id, **node_data)
        await self.save()

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
        await self.save()

    async def clear(self):
        self.graph.clear()
        await self.save()

    async def node_count(self):
        return self.graph.number_of_nodes()

    async def edge_count(self):
        return self.graph.number_of_edges()

    async def remove_node(self, node_id: object):
        if isinstance(node_id, KnwlNode):
            node_id = node_id.id

        self.graph.remove_node(node_id)
        await self.save()

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
        await self.save()

    async def get_nodes(self) -> List[KnwlNode]:
        found = list(self.graph.nodes)
        return [NetworkXGraphStorage.to_knwl_node(self.graph.nodes[node_id]) for node_id in found]

    async def get_edges(self) -> List[KnwlEdge]:
        found = list(self.graph.edges)
        return [NetworkXGraphStorage.to_knwl_edge(self.graph.edges[edge_id]) for edge_id in found]

    async def get_edge_weight(self, source_node_id: object, target_node_id: str = None) -> float:
        if isinstance(source_node_id, KnwlEdge):
            return source_node_id.weight
        if not self.graph.has_edge(source_node_id, target_node_id):
            raise ValueError(f"Edge {source_node_id} -> {target_node_id} does not exist")
        return self.graph.get_edge_data(source_node_id, target_node_id).get("weight", 1.0)

    async def unsave(self) -> None:
        if os.path.exists(self.path) and not self.memory:
            shutil.rmtree(os.path.dirname(self.path))

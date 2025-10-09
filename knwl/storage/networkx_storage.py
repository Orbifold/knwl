import shutil
from dataclasses import field, dataclass
from typing import cast
from uuid import uuid4

import networkx as nx
from pydantic import BaseModel

from knwl.logging import log
from knwl.storage.graph_base import GraphBase
from knwl.utils import *


@dataclass
class EdgeSpecs:
    id: str | None = None
    source_id: str | None = None
    target_id: str | None = None
    edge_data: dict = field(default_factory=dict)


class NetworkXGraphStorage(GraphBase):
    """
    A class to handle storage and manipulation of a directed multi-graph using NetworkX.

        - the id of nodes and edges is a uuid4 string but one could also use the combination name+type as a primary key.
        - the graph is strongly type with in/out based on BaseModel and BaseModel dataclasses, the underlying storage is however based on a dictionary. In this sense, this is a semantic layer (business data rather than storage data) above the actual graph storage.
        - this is not a semantic API in the sense that consolidation of node/edge content (descriptions) is not done here, this is a pure storage layer.

    """

    graph: nx.MultiGraph

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self.memory = (len(args) == 1 and args[0] == "memory") or self.get_param(["graph", "nx", "memory"], args, kwargs, default=False, override=config)
        self.path = self.get_param(["graph", "nx", "path"], args, kwargs, default="$test/vector", override=config, )
        self.format = self.get_param(["graph", "nx", "format"], args, kwargs, default="graphml", override=config)
        if not self.memory and self.path is not None:
            if not self.path.endswith(".graphml"):
                log.warn(f"The configured path '{self.path}' does not end with '.graphml'. Appending the extension.")
                self.path += ".graphml"
            self.path = get_full_path(self.path)
            if os.path.exists(self.path):
                preloaded_graph = NetworkXGraphStorage.load(self.path)
                if preloaded_graph is not None:
                    log.info(f"Loaded graph from {self.path} with {preloaded_graph.number_of_nodes()} nodes, {preloaded_graph.number_of_edges()} edges")
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
                    self.graph = nx.MultiDiGraph()
            else:
                self.graph = nx.MultiDiGraph()
        else:
            self.graph = nx.MultiDiGraph()  # allow multiple edges between two nodes with different labels
            self.path = None

    @staticmethod
    def get_id(data: str | BaseModel | dict | None) -> str | None:
        if data is None:
            return None
        if isinstance(data, str):
            return str.strip(data)
        if isinstance(data, BaseModel):
            return cast(BaseModel, data).id
        if isinstance(data, dict):
            if "id" in data:
                return data["id"]
            else:
                raise ValueError("NetworkXStorage: dict must contain an 'id' key")
        raise ValueError("NetworkXStorage: id must be a string, a dict or a Pydantic model")

    @staticmethod
    def get_payload(data):
        if data is None:
            raise ValueError("NetworkXStorage: payload must be a string, a dict or a Pydantic model")
        if isinstance(data, dict):
            return data
        if isinstance(data, BaseModel):
            return cast(BaseModel, data).model_dump(mode="json")
        raise ValueError("NetworkXStorage: payload must be a dict or a Pydantic model")

    @staticmethod
    def get_type(data):
        if data is None:
            return None
        if isinstance(data, str):
            return str.strip(data)
        if isinstance(data, BaseModel):
            return cast(BaseModel, data).type
        if isinstance(data, dict):
            return data.get("type", None)
        raise ValueError("NetworkXStorage: type must be a string, a dict or a Pydantic model")

    @staticmethod
    def validate_payload(payload):
        if payload is None:
            raise ValueError("NetworkXStorage: payload cannot be None")
        if not isinstance(payload, dict):
            raise ValueError("NetworkXStorage: custom data must be a dict")
        for key, value in payload.items():
            if not isinstance(key, str):
                raise ValueError("NetworkXStorage: custom data keys must be strings")
            if not isinstance(value, (str, int, float, bool, list)) and value is not None:
                raise ValueError("NetworkXStorage: custom data values must be strings, numbers, booleans, lists or dicts")

    @staticmethod
    def get_edge_specs(source, target=None) -> EdgeSpecs:
        """
        Handles all 16 combinations of (None, str, dict, BaseModel) for source and target parameters.
        Returns an EdgeSpecs object with id, source_id, target_id, and edge_data.
        Either you get
        - an error
        - an edge id (id)
        - a source_id and target_id
        - or both (id, source_id, target_id)
        """

        def extract_from_dict(data: dict):
            """Extract edge fields from dictionary"""
            return (data.get("id", None), data.get("source_id", None), data.get("target_id", None), data)

        def extract_from_basemodel(model: BaseModel):
            """Extract edge fields from BaseModel"""
            data = model.model_dump(mode="json")
            return (data.get("id", None), data.get("source_id", None), data.get("target_id", None), data)

        def parse_tuple_string(s: str):
            """Parse string in format '(source_id, target_id)' or return None"""
            match = re.match(r"\((.*?),(.*?)\)", s)
            if match:
                source_id, target_id = match.groups()
                return str.strip(source_id), str.strip(target_id)
            return None

        def validate_ids(source_id: str, target_id: str):
            """Validate source and target IDs"""
            if source_id == target_id:
                raise ValueError("NetworkXStorage: source and target node ids must be different")
            if source_id == "":
                raise ValueError("NetworkXStorage: source node id must not be empty")
            if target_id == "":
                raise ValueError("NetworkXStorage: target node id must not be empty")

        # Handle all 16 combinations systematically

        # ============================================================================================
        # SOURCE = None (4 combinations)
        # ============================================================================================
        if source is None:
            if target is None:
                # (None, None)
                return EdgeSpecs(id=None, source_id=None, target_id=None, edge_data={})

            elif isinstance(target, str):
                # (None, str) - try to parse as tuple string, otherwise treat as edge ID
                parsed = parse_tuple_string(target)
                if parsed:
                    source_id, target_id = parsed
                    validate_ids(source_id, target_id)
                    return EdgeSpecs(id=None, source_id=source_id, target_id=target_id, edge_data={})
                else:
                    return EdgeSpecs(id=target, source_id=None, target_id=None, edge_data={})

            elif isinstance(target, dict):
                # (None, dict)
                id, source_id, target_id, edge_data = extract_from_dict(target)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

            elif isinstance(target, BaseModel):
                # (None, BaseModel)
                id, source_id, target_id, edge_data = extract_from_basemodel(target)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

        # ============================================================================================
        # SOURCE = str (4 combinations)
        # ============================================================================================
        elif isinstance(source, str):
            if target is None:
                # (str, None) - try to parse as tuple string, otherwise treat as edge ID
                parsed = parse_tuple_string(source)
                if parsed:
                    source_id, target_id = parsed
                    validate_ids(source_id, target_id)
                    return EdgeSpecs(id=None, source_id=source_id, target_id=target_id, edge_data={})
                else:
                    return EdgeSpecs(id=source, source_id=None, target_id=None, edge_data={})

            elif isinstance(target, str):
                # (str, str) - source and target IDs
                source_id = str.strip(source)
                target_id = str.strip(target)
                validate_ids(source_id, target_id)
                return EdgeSpecs(id=None, source_id=source_id, target_id=target_id, edge_data={})

            elif isinstance(target, dict):
                # (str, dict) - source ID from string, merge with dict data
                id, _, target_id, edge_data = extract_from_dict(target)
                source_id = str.strip(source)
                if target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

            elif isinstance(target, BaseModel):
                # (str, BaseModel) - source ID from string, data from BaseModel
                id, _, target_id, edge_data = extract_from_basemodel(target)
                source_id = str.strip(source)
                if target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

        # ============================================================================================
        # SOURCE = dict (4 combinations)
        # ============================================================================================
        elif isinstance(source, dict):
            if target is None:
                # (dict, None)
                id, source_id, target_id, edge_data = extract_from_dict(source)
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

            elif isinstance(target, str):
                # (dict, str) - merge dict data with target ID from string
                id, source_id, _, edge_data = extract_from_dict(source)
                target_id = str.strip(target)
                if source_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

            elif isinstance(target, dict):
                # (dict, dict) - merge both dictionaries
                id1, source_id, _, edge_data1 = extract_from_dict(source)
                id2, _, target_id, edge_data2 = extract_from_dict(target)
                id = id1 or id2  # Prefer source dict's ID
                merged_data = {**edge_data1, **edge_data2}
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=merged_data)

            elif isinstance(target, BaseModel):
                # (dict, BaseModel) - merge dict with BaseModel data
                id1, source_id, _, edge_data1 = extract_from_dict(source)
                id2, _, target_id, edge_data2 = extract_from_basemodel(target)
                id = id1 or id2  # Prefer source dict's ID
                merged_data = {**edge_data1, **edge_data2}
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=merged_data)

        # ============================================================================================
        # SOURCE = BaseModel (4 combinations)
        # ============================================================================================
        elif isinstance(source, BaseModel):
            if target is None:
                # (BaseModel, None)
                id, source_id, target_id, edge_data = extract_from_basemodel(source)
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

            elif isinstance(target, str):
                # (BaseModel, str) - BaseModel data with target ID from string
                id, source_id, _, edge_data = extract_from_basemodel(source)
                target_id = str.strip(target)
                if source_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=edge_data)

            elif isinstance(target, dict):
                # (BaseModel, dict) - merge BaseModel with dict data
                id1, source_id, _, edge_data1 = extract_from_basemodel(source)
                id2, _, target_id, edge_data2 = extract_from_dict(target)
                id = id1 or id2  # Prefer source BaseModel's ID
                merged_data = {**edge_data1, **edge_data2}
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=merged_data)

            elif isinstance(target, BaseModel):
                # (BaseModel, BaseModel) - merge both BaseModels
                id1, source_id, _, edge_data1 = extract_from_basemodel(source)
                id2, _, target_id, edge_data2 = extract_from_basemodel(target)
                id = id1 or id2  # Prefer source BaseModel's ID
                merged_data = {**edge_data1, **edge_data2}
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(id=id, source_id=source_id, target_id=target_id, edge_data=merged_data)

        # Fallback case (should not reach here with proper type checking)
        return EdgeSpecs(id=None, source_id=None, target_id=None, edge_data={})

    @staticmethod
    def load(file_name) -> nx.Graph | None:
        try:
            if os.path.exists(file_name):
                return nx.read_graphml(file_name)
        except Exception as e:
            log.error(f"Error loading graph from {file_name}: {e}")
            return None

    @staticmethod
    def write(graph: nx.Graph, file_name):
        log.info(f"Writing graph with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
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
        specs = NetworkXGraphStorage.get_edge_specs(source_or_key, target_node_id)
        if specs.id is not None:
            return self.get_edge_by_id(specs.id) is not None
        else:
            return self.graph.has_edge(specs.source_id, specs.target_id)

    async def get_node_by_id(self, node_id: str) -> Union[dict, None]:
        found = self.graph.nodes.get(node_id)
        if found:
            found["id"] = node_id
            return found
        else:
            return None

    async def get_node_by_name(self, node_name: str) -> Union[List[dict], None]:
        found = []
        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            if node.get("name", None) == node_name:
                node["id"] = node_id
                found.append(node)
        return found

    async def node_degree(self, node_id: str) -> int:
        return self.graph.degree(node_id)

    async def edge_degree(self, source_id: str, target_id: str) -> int:
        return self.graph.degree(source_id) + self.graph.degree(target_id)

    async def get_edges(self, source_node_id_or_key: str, target_node_id: str = None, type: str = None) -> Union[list[dict], None]:
        specs = NetworkXGraphStorage.get_edge_specs(source_node_id_or_key, target_node_id)
        if specs.id is not None:
            edge = await self.get_edge_by_id(specs.id)
            return [edge] if edge else []
        elif specs.source_id is not None and specs.target_id is not None:
            edges = []
            for u, v, data in self.graph.edges(data=True):
                if u == specs.source_id and v == specs.target_id:
                    edge_data = {"source_id": u, "target_id": v, **data}
                    if type is None or edge_data.get("type") == type:
                        edges.append(edge_data)
            return edges
        else:
            return None

    async def get_node_edges(self, source_node_id: str) -> List[dict] | None:
        """
        Retrieves all edges connected to the given node.

        Args:
            source_node_id (str): The ID of the source node.

        Returns:
            List[BaseModel] | None: A list of BaseModel objects if the node exists, None otherwise.
        """
        if await self.node_exists(source_node_id):
            tuples = list(self.graph.edges(source_node_id))

            raw = [{"source_id": t[0], "target_id": t[1], **self.graph.get_edge_data(t[0], t[1], {})} for t in tuples]
            return raw
        return None

    async def get_attached_edges(self, nodes: List[str]) -> List[dict]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (List[BaseModel]): A list of BaseModel objects for which to retrieve attached edges.

        Returns:
            List[BaseModel]: A list of BaseModel objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])
        edges = []
        for n in nodes:
            n_edges = await self.get_node_edges(n.id)
            # ensure the list is unique based on the id of BaseModel
            edges.extend([e for e in n_edges if e is not None and e.id not in [ee.id for ee in edges]])
        return edges

    async def get_edge_degrees(self, edges: List[dict]) -> List[int]:
        """
        Asynchronously retrieves the degrees of the given edges.

        Args:
            edges (List[BaseModel]): A list of BaseModel objects for which to retrieve degrees.

        Returns:
            List[int]: A list of degrees for the given edges.
        """
        return await asyncio.gather(*[self.edge_degree(e.source_id, e.target_id) for e in edges])

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
            source_id = e.source_id
            target_id = e.target_id
            source_node = await self.get_node_by_id(source_id)
            target_node = await self.get_node_by_id(target_id)
            if source_node and target_node:
                coll[e.id] = (source_node.name, target_node.name)
        return coll

    async def get_edge_by_id(self, edge_id: str) -> dict | None:
        for edge in self.graph.edges(data=True):
            if edge[2]["id"] == edge_id:
                found = edge[2]
                found["id"] = edge_id

                return found
        raise ValueError(f"Edge with id {edge_id} not found")

    async def BaseModel(self, node_id: BaseModel | str | dict, node_data: object = None):
        if node_id is None:
            raise ValueError("NetworkXStorage: you need an id to upsert node")

        if node_data is None:
            if isinstance(node_id, BaseModel):
                node_data = node_id.model_dump(mode="json")
                node_id = node_data.get("id", node_id)
            elif isinstance(node_id, dict):
                node_data = cast(dict, node_id)
                node_id = node_data.get("id", str(uuid4()))
            elif isinstance(node_id, str):
                node_data = {}
                node_id = str.strip(node_id)
        else:
            if not isinstance(node_id, str):
                raise ValueError("NetworkXStorage: if node data is provided the node Id must be a string")
            if str.strip(node_id) == "":
                raise ValueError("NetworkXStorage: node Id must not be empty")
            if isinstance(node_data, BaseModel):
                node_data = node_data.model_dump(mode="json")
            elif isinstance(node_data, dict):
                node_data = cast(dict, node_data)
            else:
                raise ValueError("NetworkXStorage: node data must be a dict or a Pydantic model")

        node_data["id"] = node_id
        self.validate_payload(node_data)
        self.graph.add_node(node_id, **node_data)
        await self.save()

    async def upsert_edge(self, source_node_id, target_node_id, edge_data=None):
        specs = NetworkXGraphStorage.get_edge_specs(source_node_id, target_node_id)
        edge_id = None
        source_id = specs.source_id
        target_id = specs.target_id
        type = None
        if specs.id is None:
            if edge_data is None:
                raise ValueError("NetworkXStorage: you need an id to upsert edge")
            else:
                edge_id = self.get_id(edge_data)
                if edge_id is None:
                    raise ValueError("NetworkXStorage: edge id cannot be None, use the edge data to specify the id.")
        else:
            edge_id = specs.id
        if edge_data is None:
            if isinstance(edge_id, str):
                raise ValueError("NetworkXStorage: you need a type to upsert edge")
            else:
                type = self.get_type(edge_id)
        else:
            type = self.get_type(edge_data)
        if type is None or str.strip(type) == "":
            raise ValueError("NetworkXStorage: edge type cannot be None or empty")
        # upsert
        found = self.graph.get_edge_data(source_id, target_id)
        found_edge_id = None
        if found:
            for key in found:
                if found[key].get("type", None) == type:
                    found_edge_id = found[key].get("id", edge_id)
                    break

        if found_edge_id is None:
            self.graph.add_edge(source_node_id, target_node_id, key=type, **edge_data)  # the key is the way nx distinguishes multiple edges between two nodes
        else:
            if found_edge_id == edge_id:
                # update the edge
                self.graph.remove_edge(source_node_id, target_node_id, key=type)
                self.graph.add_edge(source_id, target_id, key=type, **edge_data)
            else:
                raise ValueError("NetworkXStorage: edge with different id and same type already exists between these nodes")
        await self.save()

    async def clear(self):
        self.graph.clear()
        await self.save()

    async def node_count(self):
        return self.graph.number_of_nodes()

    async def edge_count(self):
        return self.graph.number_of_edges()

    async def remove_node(self, node_id: object):
        if isinstance(node_id, BaseModel):
            node_id = node_id.id

        self.graph.remove_node(node_id)
        await self.save()

    async def remove_edge(self, source_node_id: object, target_node_id: str = None):
        source_id = None
        target_id = None
        if isinstance(source_node_id, BaseModel):
            source_id = source_node_id.source_id
            target_id = source_node_id.target_id
        if isinstance(source_node_id, tuple):
            source_id, target_id = source_node_id
        if isinstance(source_node_id, BaseModel):
            source_id = source_node_id.id
        if isinstance(target_node_id, BaseModel):
            target_id = target_node_id.id
        if isinstance(source_node_id, str):
            source_id = source_node_id
            if target_node_id is None:
                raise ValueError("Insufficient data to remove edge, missing target node id")
            else:
                target_id = target_node_id
        self.graph.remove_edge(source_id, target_id)
        await self.save()

    async def get_edge_weight(self, source_node_id: object, target_node_id: str = None) -> float:
        if isinstance(source_node_id, BaseModel):
            return source_node_id.weight
        if not self.graph.has_edge(source_node_id, target_node_id):
            raise ValueError(f"Edge {source_node_id} -> {target_node_id} does not exist")
        return self.graph.get_edge_data(source_node_id, target_node_id).get("weight", 1.0)

    async def unsave(self) -> None:
        if os.path.exists(self.path) and not self.memory:
            shutil.rmtree(os.path.dirname(self.path))

    async def upsert_node(self, node_id: Union[BaseModel, str, dict], node_data=None):
        if node_id is None:
            raise ValueError("NetworkXStorage: you need an id to upsert node")
        else:
            id = self.get_id(node_id)
            if id is None:
                raise ValueError("NetworkXStorage: you need an id to upsert node")
            if not isinstance(node_id, str):
                node_data = self.get_payload(node_id)
            else:
                node_data = self.get_payload(node_data)
            self.validate_payload(node_data)
            if "id" in node_data and isinstance(node_id, str):
                if not isinstance(node_data["id"], str):
                    raise ValueError("NetworkXStorage: node id in data must be a string")
                if node_data["id"] != id:
                    raise ValueError("NetworkXStorage: node id in data does not match the provided node id")
            node_data["id"] = id
            # add_node will update if the node-id already exists
            self.graph.add_node(id, **node_data)

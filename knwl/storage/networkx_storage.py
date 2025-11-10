import shutil
import warnings
from dataclasses import field, dataclass
from typing import cast

import networkx as nx
from pydantic import BaseModel

from knwl.di import defaults
from knwl.logging import log
from knwl.storage.graph_base import GraphStorageBase
from knwl.utils import *


@dataclass
class EdgeSpecs:
    id: str | None = None
    source_id: str | None = None
    target_id: str | None = None
    edge_data: dict = field(default_factory=dict)


@defaults("graph", "user")
class NetworkXGraphStorage(GraphStorageBase):
    """
    A class to handle storage and manipulation of a directed multi-graph using NetworkX.

        - the id of nodes and edges is a uuid4 string but one could also use the combination name+type as a primary key.
        - the graph is strongly type with in/out based on BaseModel and BaseModel dataclasses, the underlying storage is however based on a dictionary. In this sense, this is a semantic layer (business data rather than storage data) above the actual graph storage.
        - this is not a semantic API in the sense that consolidation of node/edge content (descriptions) is not done here, this is a pure storage layer.

    """

    graph: nx.MultiDiGraph

    def __init__(self, path: str = "memory", format: str = "graphml"):
        super().__init__()
        self._in_memory = path is None or str(path).strip().lower() == "memory"
        self._path = path
        self._format = format

        if not self._in_memory and self._path is not None:
            if not self._path.endswith(".graphml"):
                log.warn(
                    f"The configured path '{self._path}' does not end with '.graphml'. Appending the extension."
                )
                self._path += ".graphml"
            self._path = get_full_path(self._path)
            if os.path.exists(self._path):
                preloaded_graph = NetworkXGraphStorage.load(self._path)
                if preloaded_graph is not None:
                    log.info(
                        f"Loaded graph from {self._path} with {preloaded_graph.number_of_nodes()} nodes, {preloaded_graph.number_of_edges()} edges"
                    )
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
            self.graph = (
                nx.MultiDiGraph()
            )  # allow multiple edges between two nodes with different labels
            self._path = None

    @property
    def path(self):
        return self._path

    @property
    def in_memory(self):
        return self._in_memory

    @staticmethod
    def to_edge(obj) -> dict:
        if isinstance(obj, dict):
            return cast(dict, obj)
        if isinstance(obj, BaseModel):
            return cast(BaseModel, obj).model_dump(mode="json")
        if isinstance(obj, tuple):
            if len(obj) >= 3:
                return {
                    "source_id": obj[0],
                    "target_id": obj[1],
                    **(obj[2] if isinstance(obj[2], dict) else {}),
                }
            raise TypeError(f"Like not an edge {type(obj)}")
        raise ValueError("NetworkXStorage: edge must be a dict or a Pydantic model")

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
        raise ValueError(
            "NetworkXStorage: id must be a string, a dict or a Pydantic model"
        )

    @staticmethod
    def get_payload(data):
        if data is None:
            raise ValueError(
                "NetworkXStorage: payload must be a string, a dict or a Pydantic model"
            )
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
        raise ValueError(
            "NetworkXStorage: type must be a string, a dict or a Pydantic model"
        )

    @staticmethod
    def validate_payload(payload):
        if payload is None:
            raise ValueError("NetworkXStorage: payload cannot be None")
        if not isinstance(payload, dict):
            raise ValueError("NetworkXStorage: custom data must be a dict")
        for key, value in payload.items():
            if not isinstance(key, str):
                raise ValueError("NetworkXStorage: custom data keys must be strings")
            if (
                not isinstance(value, (str, int, float, bool, list))
                and value is not None
            ):
                if isinstance(value, dict):
                    payload[key] = json.dumps(value)
                elif isinstance(value, BaseModel):
                    payload[key] = json.dumps(
                        cast(BaseModel, value).model_dump(mode="json")
                    )
                else:
                    raise ValueError(
                        "NetworkXStorage: custom data values must be strings, numbers, booleans, lists or dicts"
                    )

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
            return (
                data.get("id", None),
                data.get("source_id", None),
                data.get("target_id", None),
                data,
            )

        def extract_from_basemodel(model: BaseModel):
            """Extract edge fields from BaseModel"""
            data = model.model_dump(mode="json")
            return (
                data.get("id", None),
                data.get("source_id", None),
                data.get("target_id", None),
                data,
            )

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
                raise ValueError(
                    "NetworkXStorage: source and target node ids must be different"
                )
            if source_id == "":
                raise ValueError("NetworkXStorage: source node id must not be empty")
            if target_id == "":
                raise ValueError("NetworkXStorage: target node id must not be empty")

        # Handle all 17 combinations systematically
        if isinstance(source, tuple):
            if target is not None:
                raise ValueError(
                    "NetworkXStorage: when source is a tuple, target must be None"
                )
            if len(source) != 2:
                raise ValueError(
                    "NetworkXStorage: when source is a tuple, it must have exactly two elements (source_id, target_id)"
                )
            source_id, target_id = source
            if not isinstance(source_id, str) or not isinstance(target_id, str):
                raise ValueError(
                    "NetworkXStorage: when source is a tuple, both elements must be strings (source_id, target_id)"
                )
            validate_ids(source_id, target_id)
            return EdgeSpecs(
                id=None, source_id=source_id, target_id=target_id, edge_data={}
            )
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
                    return EdgeSpecs(
                        id=None, source_id=source_id, target_id=target_id, edge_data={}
                    )
                else:
                    return EdgeSpecs(
                        id=target, source_id=None, target_id=None, edge_data={}
                    )

            elif isinstance(target, dict):
                # (None, dict)
                id, source_id, target_id, edge_data = extract_from_dict(target)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

            elif isinstance(target, BaseModel):
                # (None, BaseModel)
                id, source_id, target_id, edge_data = extract_from_basemodel(target)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

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
                    return EdgeSpecs(
                        id=None, source_id=source_id, target_id=target_id, edge_data={}
                    )
                else:
                    return EdgeSpecs(
                        id=source, source_id=None, target_id=None, edge_data={}
                    )

            elif isinstance(target, str):
                # (str, str) - source and target IDs
                source_id = str.strip(source)
                target_id = str.strip(target)
                validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=None, source_id=source_id, target_id=target_id, edge_data={}
                )

            elif isinstance(target, dict):
                # (str, dict) - source ID from string, merge with dict data
                id, _, target_id, edge_data = extract_from_dict(target)
                source_id = str.strip(source)
                if target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

            elif isinstance(target, BaseModel):
                # (str, BaseModel) - source ID from string, data from BaseModel
                id, _, target_id, edge_data = extract_from_basemodel(target)
                source_id = str.strip(source)
                if target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

        # ============================================================================================
        # SOURCE = dict (4 combinations)
        # ============================================================================================
        elif isinstance(source, dict):
            if target is None:
                # (dict, None)
                id, source_id, target_id, edge_data = extract_from_dict(source)
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

            elif isinstance(target, str):
                # (dict, str) - merge dict data with target ID from string
                id, source_id, _, edge_data = extract_from_dict(source)
                target_id = str.strip(target)
                if source_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

            elif isinstance(target, dict):
                # (dict, dict) - merge both dictionaries
                id1, source_id, _, edge_data1 = extract_from_dict(source)
                id2, _, target_id, edge_data2 = extract_from_dict(target)

                return EdgeSpecs(id=None, source_id=id1, target_id=id2, edge_data=None)

            elif isinstance(target, BaseModel):
                # (dict, BaseModel) - merge dict with BaseModel data
                id1, source_id, _, edge_data1 = extract_from_dict(source)
                id2, _, target_id, edge_data2 = extract_from_basemodel(target)
                id = id1 or id2  # Prefer source dict's ID
                merged_data = {**edge_data1, **edge_data2}
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id,
                    source_id=source_id,
                    target_id=target_id,
                    edge_data=merged_data,
                )

        # ============================================================================================
        # SOURCE = BaseModel (4 combinations)
        # ============================================================================================
        elif isinstance(source, BaseModel):
            if target is None:
                # (BaseModel, None)
                id, source_id, target_id, edge_data = extract_from_basemodel(source)
                if source_id and target_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

            elif isinstance(target, str):
                # (BaseModel, str) - BaseModel data with target ID from string
                id, source_id, _, edge_data = extract_from_basemodel(source)
                target_id = str.strip(target)
                if source_id:
                    validate_ids(source_id, target_id)
                return EdgeSpecs(
                    id=id, source_id=source_id, target_id=target_id, edge_data=edge_data
                )

            elif isinstance(target, dict):
                # (BaseModel, dict) - merge BaseModel with dict data
                id1, source_id, _, edge_data1 = extract_from_basemodel(source)
                id2, _, target_id, edge_data2 = extract_from_dict(target)

                return EdgeSpecs(id=None, source_id=id1, target_id=id2, edge_data={})

            elif isinstance(target, BaseModel):
                # (BaseModel, BaseModel) - merge both BaseModels
                id1, source_id, _, edge_data1 = extract_from_basemodel(source)
                id2, _, target_id, edge_data2 = extract_from_basemodel(target)

                return EdgeSpecs(id=None, source_id=id1, target_id=id2, edge_data={})

        # Fallback case (should not reach here with proper type checking)
        return EdgeSpecs(id=None, source_id=None, target_id=None, edge_data={})

    @staticmethod
    def load(file_name) -> nx.MultiDiGraph | None:
        try:
            if os.path.exists(file_name):
                return nx.read_graphml(file_name, force_multigraph=True)
        except Exception as e:
            log.error(f"Error loading graph from {file_name}: {e}")
            return None

    @staticmethod
    def write(graph: nx.Graph, file_name):
        log.info(
            f"Writing graph with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges"
        )
        # the label is the name, helps with visualization
        nx.set_node_attributes(
            graph, {id: graph.nodes[id].get("name", id) for id in graph.nodes}, "label"
        )

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

        nx.write_graphml(graph, file_name, infer_numeric_types=True)

    async def save(self):
        if not self._in_memory and self._path is not None:
            NetworkXGraphStorage.write(self.graph, self._path)

    async def node_exists(self, node_id: str) -> bool:
        if str.strip(node_id) == "":
            return False
        return self.graph.has_node(node_id)

    async def edge_exists(
        self,
        source_or_key: Union[BaseModel, str, dict],
        target_node_id: Union[BaseModel, str, dict] = None,
    ) -> bool:
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

    async def get_nodes_by_name(self, node_name: str) -> Union[list[dict], None]:
        found = []
        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            if node.get("name", None) == node_name:
                node["id"] = node_id
                found.append(node)
        return found

    async def node_degree(self, node_id: str) -> int:
        return self.graph.degree(node_id)

    async def edge_degree(self, edge_or_source_id: str, target_id: str = None) -> int:
        if target_id is None:
            edge = await self.get_edge_by_id(edge_or_source_id)
            if edge is None:
                raise KeyError(
                    f"edge_degree: edge with id {edge_or_source_id} not found"
                )
            target_id = edge["target_id"]
            source_id = edge["source_id"]
        else:
            source_id = str.strip(edge_or_source_id)
            target_id = str.strip(target_id)

        return int(self.graph.degree(source_id)) + int(self.graph.degree(target_id))

    async def get_edges(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ) -> Union[list[dict], None]:
        specs = NetworkXGraphStorage.get_edge_specs(
            source_node_id_or_key, target_node_id
        )
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

    async def get_node_edges(self, source_node_id: str) -> list[dict] | None:
        """
        Retrieves all edges connected to the given node.

        Args:
            source_node_id (str): The ID of the source node.

        Returns:
            list[BaseModel] | None: A list of BaseModel objects if the node exists, None otherwise.
        """
        if await self.node_exists(source_node_id):
            es = list(self.graph.edges(source_node_id, data=True))
            return [self.to_edge(e) for e in es]
        return None

    async def get_attached_edges(self, nodes: list[str]) -> list[dict]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (list[BaseModel]): A list of BaseModel objects for which to retrieve attached edges.

        Returns:
            list[BaseModel]: A list of BaseModel objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])
        edges = []
        for n in nodes:
            n_edges = await self.get_node_edges(n.id)
            # ensure the list is unique based on the id of BaseModel
            edges.extend(
                [
                    e
                    for e in n_edges
                    if e is not None and e["id"] not in [ee["id"] for ee in edges]
                ]
            )
        return edges

    async def get_edge_degrees(self, edges: list[dict]) -> list[int]:
        """
        Asynchronously retrieves the degrees of the given edges.

        Args:
            edges (list[BaseModel]): A list of BaseModel objects for which to retrieve degrees.

        Returns:
            list[int]: A list of degrees for the given edges.
        """
        return await asyncio.gather(
            *[self.edge_degree(e.source_id, e.target_id) for e in edges]
        )

    async def get_semantic_endpoints(
        self, edge_ids: list[str]
    ) -> dict[str, tuple[str, str]]:
        """
        Asynchronously retrieves the names of the nodes with the given IDs.

        Args:
            edge_ids (list[str]): A list of node IDs for which to retrieve names.

        Returns:
            list[str]: A list of node names.
        """
        edges = await asyncio.gather(*[self.get_edge_by_id(id) for id in edge_ids])
        coll = {}
        for e in edges:
            source_id = e["source_id"]
            target_id = e["target_id"]
            source_node = await self.get_node_by_id(source_id)
            target_node = await self.get_node_by_id(target_id)
            if source_node and target_node:
                coll[e["id"]] = (source_node["name"], target_node["name"])
        return coll

    async def get_edge_by_id(self, edge_id: str) -> dict | None:
        for edge in self.graph.edges(data=True):
            if edge[2]["id"] == edge_id:
                found = edge[2]
                found["id"] = edge_id

                return found
        raise ValueError(f"Edge with id {edge_id} not found")

    async def get_edges_between_nodes(
        self, source_id: str, target_id: str
    ) -> list[dict]:
        edges = []
        for u, v, data in self.graph.edges(data=True):
            if u == source_id and v == target_id:
                edge_data = {"source_id": u, "target_id": v, **data}
                edges.append(edge_data)
        return edges

    async def upsert_edge(self, source_node_id, target_node_id=None, edge_data=None):
        # Parse edge specifications
        specs = NetworkXGraphStorage.get_edge_specs(source_node_id, target_node_id)

        # Validate we have the minimum required information
        if specs.source_id is None or specs.target_id is None:
            raise ValueError(
                "NetworkXStorage: source_id and target_id are required to upsert edge"
            )

        source_id = specs.source_id
        target_id = specs.target_id
        edge_type = "Unknown"

        # Determine edge data and validate it
        if edge_data is None:
            if specs.edge_data:
                edge_data = specs.edge_data
            else:
                edge_data = {}
        else:
            # Merge provided edge_data with specs.edge_data, giving priority to provided data
            merged_data = {**(specs.edge_data or {}), **self.get_payload(edge_data)}
            edge_data = merged_data
            edge_type = edge_data.get("type", "Unknown")

        # Validate edge data
        self.validate_payload(edge_data)

        # Determine edge ID
        edge_id = specs.id or edge_data.get("id")
        if edge_id is None:
            edge_type = edge_data.get("type", "Unknown")
            edge_id = hash_with_prefix(
                {"source_id": source_id, "target_id": target_id, "type": edge_type},
                prefix="edge|>",
            )

        # Ensure edge has required fields
        edge_data["id"] = edge_id
        edge_data["source_id"] = source_id
        edge_data["target_id"] = target_id

        if await self.get_node_by_id(source_id) is None:
            raise ValueError(
                f"NetworkXStorage: source node with id '{source_id}' does not exist"
            )
        if await self.get_node_by_id(target_id) is None:
            raise ValueError(
                f"NetworkXStorage: target node with id '{target_id}' does not exist"
            )

        # Get edge type for NetworkX key
        # edge_type = edge_data.get("type", "Unknown")
        if not edge_type or str.strip(edge_type) == "":
            edge_type = "Unknown"
        edge_data["type"] = edge_type

        # Check if edge already exists with same type
        existing_edges = self.graph.get_edge_data(source_id, target_id, key=None)
        existing_edge_key = None

        if existing_edges:
            for key, data in existing_edges.items():
                if data.get("type") == edge_type:
                    existing_edge_key = key
                    existing_edge_id = data.get("id")
                    # If same edge ID, we can update; if different ID but same type, that's an error
                    if existing_edge_id and existing_edge_id != edge_id:
                        raise ValueError(
                            f"NetworkXStorage: edge with different id '{existing_edge_id}' "
                            f"but same type '{edge_type}' already exists between nodes {source_id} -> {target_id}"
                        )
                    break

        # Remove existing edge if found (for update)
        if existing_edge_key is not None:
            self.graph.remove_edge(source_id, target_id, key=edge_type)

        # Add the edge with type as key
        self.graph.add_edge(source_id, target_id, key=edge_type, **edge_data)

        await self.save()
        return {"source_id": source_id, "target_id": target_id, **edge_data}

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
        elif isinstance(node_id, dict):
            node_id = node_id.get("id")
        elif isinstance(node_id, str):
            node_id = str(node_id).strip()
        else:
            raise ValueError(f"remove_node: unknown node type {node_id}")

        self.graph.remove_node(node_id)
        await self.save()

    async def remove_edge(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ):
        specs = NetworkXGraphStorage.get_edge_specs(
            source_node_id_or_key, target_node_id
        )
        if specs.id is not None:
            edge = await self.get_edge_by_id(specs.id)
            if edge is None:
                raise ValueError(
                    f"NetworkXStorage: edge with id '{specs.id}' does not exist"
                )
            source_id = edge["source_id"]
            target_id = edge["target_id"]
        elif specs.source_id is not None and specs.target_id is not None:
            source_id = specs.source_id
            target_id = specs.target_id
        else:
            raise ValueError(
                "NetworkXStorage: source_id and target_id are required to remove edge"
            )
        if type is not None:
            self.graph.remove_edge(source_id, target_id, key=type)
        else:
            found = await self.get_edges(source_id, target_id)
            if len(found) == 1:
                edge_type = found[0].get("type", "Unknown")
                self.graph.remove_edge(source_id, target_id, key=edge_type)
            elif len(found) > 1:
                raise ValueError(
                    f"NetworkXStorage: multiple edges found between {source_id} and {target_id}, please specify the type to remove a specific edge"
                )
            else:
                raise ValueError(
                    f"NetworkXStorage: no edge found between {source_id} and {target_id}"
                )
        await self.save()

    async def get_edge_weights(
        self, source_node_id_or_key: str, target_node_id: str = None, type: str = None
    ) -> dict[str, float]:
        specs = NetworkXGraphStorage.get_edge_specs(
            source_node_id_or_key, target_node_id
        )
        edges = await self.get_edges(specs.source_id, specs.target_id, type)
        weights = {}
        for edge in edges:
            weight = edge.get("weight", 1.0)
            if not isinstance(weight, (int, float)):
                try:
                    weight = float(weight)
                except ValueError:
                    weight = 1.0
            weights[edge["type"]] = weight
        return weights

    async def unsave(self) -> None:
        if os.path.exists(self._path) and not self._in_memory:
            shutil.rmtree(os.path.dirname(self._path))

    async def upsert_node(self, node_id: Union[BaseModel, str, dict], node_data=None):
        if node_id is None:
            raise ValueError("NetworkXStorage: you need an id to upsert node")
        else:
            if isinstance(node_id, str):
                # Case 1: node_id is a string
                id = str.strip(node_id)
                if id == "":
                    raise ValueError("NetworkXStorage: node id must not be empty")
                if node_data is None:
                    node_data = {}
                else:
                    node_data = self.get_payload(node_data)
                    second_id = node_data.get("id")
                    if "id" in node_data and node_data["id"] is None:
                        warnings.warn(
                            "NetworkXStorage: node id specified in payload is None, this is not necessary and can be removed."
                        )
                    if second_id is not None and second_id != id:
                        if isinstance(node_data, BaseModel):
                            raise ValueError(
                                "NetworkXStorage: node id mismatch. Simply add the node without the id in the first slot, upsert_node(KnwlNode(...))"
                            )
                        else:
                            raise ValueError(
                                f"NetworkXStorage: node id '{second_id}' in payload does not match the provided initial id '{id}'."
                            )

            elif isinstance(node_id, dict):
                # Case 2: node_id is a dict
                if node_data is not None:
                    raise ValueError(
                        "NetworkXStorage: when providing a dict as node_id, do not provide a second node_data parameter."
                    )
                node_data = cast(dict, node_id)
                id = node_data.get("id")
                if id is None:
                    raise ValueError("NetworkXStorage: dict must contain an 'id' key")

            elif isinstance(node_id, BaseModel):
                # Case 3: node_id is a BaseModel
                node_data = cast(BaseModel, node_id).model_dump(mode="json")
                id = node_data.get("id")
                if id is None:
                    raise ValueError(
                        "NetworkXStorage: BaseModel must have an 'id' attribute"
                    )

            else:
                raise ValueError(
                    "NetworkXStorage: node_id must be a string, dict, or BaseModel"
                )

            # Validate the final payload and add the node
            self.validate_payload(node_data)
            node_data["id"] = id
            self.graph.add_node(id, **node_data)
            await self.save()
            return {"id": id, **node_data}

    async def merge(self, nodes: list[dict], edges: list[dict]) -> None:
        for node in nodes:
            await self.upsert_node(node)
        for edge in edges:
            source_id = edge.get("source_id")
            target_id = edge.get("target_id")
            if source_id is None or target_id is None:
                raise ValueError(
                    "NetworkXStorage: edge must contain 'source_id' and 'target_id'"
                )
            await self.upsert_edge(source_id, target_id, edge)
        await self.save()

from typing import Any
from knwl.models import KnwlDocument, KnwlEdge, KnwlGraph, KnwlNode
from knwl.storage.blob_storage_base import BlobStorageBase
from knwl.storage.graph_base import GraphStorageBase
from knwl.storage.kv_storage_base import KeyValueStorageBase
from knwl.storage.vector_storage_base import VectorStorageBase


class StorageAdapter:
    """
    This sits between Knwl input formats and the diverse storage interfaces.
    It attempts to store whatever you throw at it in the appropriate storage backend.

    Define the various storage backens and map a given input to the correct storage (can be a list).
    Note that the @defaults decorator defines a preset configuration for this adapter.
    """

    def __init__(
        self,
        blob_storage: BlobStorageBase = None,
        vector_storage: VectorStorageBase = None,
        kv_storage: KeyValueStorageBase = None,
        graph_storage: GraphStorageBase = None,
    ) -> None:
        self._blob_storage = blob_storage
        self._vector_storage = vector_storage
        self._kv_storage = kv_storage
        self._graph_storage = graph_storage
        self.validate_services()

    def validate_services(self) -> None:
        if not isinstance(self._blob_storage, BlobStorageBase):
            raise ValueError(
                "StorageAdapter: blob_storage must be an instance of BlobStorageBase."
            )
        if not isinstance(self._vector_storage, VectorStorageBase):
            raise ValueError(
                "StorageAdapter: vector_storage must be an instance of VectorStorageBase."
            )
        if not isinstance(self._kv_storage, KeyValueStorageBase):
            raise ValueError(
                "StorageAdapter: kv_storage must be an instance of KeyValueStorageBase."
            )
        if not isinstance(self._graph_storage, GraphStorageBase):
            raise ValueError(
                "StorageAdapter: graph_storage must be an instance of GraphStorageBase."
            )

    @property
    def blob_storage(self) -> BlobStorageBase:
        return self._blob_storage

    @property
    def vector_storage(self) -> VectorStorageBase:
        return self._vector_storage

    @property
    def kv_storage(self) -> KeyValueStorageBase:
        return self._kv_storage

    @property
    def graph_storage(self) -> GraphStorageBase:
        return self._graph_storage

    def validate_destination(self, destination: str | list[str]) -> None:
        """
        Validate that the given destination(s) are valid storage backends.
        """
        valid_destinations = {"blob", "vector", "kv", "graph"}
        if isinstance(destination, str):
            destinations = [destination]
        else:
            destinations = destination

        for dest in destinations:
            if dest not in valid_destinations:
                raise ValueError(
                    f"StorageAdapter: Invalid destination '{dest}'. Valid destinations are: {valid_destinations}"
                )

    async def store(self, input: Any, destination: str | list[str]) -> None:
        """
        Store the given input in the appropriate storage backend(s).
        The input can be of various types, and the method will determine
        which storage backend(s) to use based on the input type.
        """
        self.validate_destination(destination)

        if isinstance(input, KnwlDocument):
            await self._blob_storage.store_document(input)
        elif isinstance(input, KnwlGraph):
            await self._graph_storage.store_graph(input)
        elif isinstance(input, KnwlNode):
            await self._vector_storage.store_node(input)
        elif isinstance(input, KnwlEdge):
            await self._kv_storage.store_edge(input)
        else:
            raise ValueError("StorageAdapter: Unsupported input type for storage.")

    async def store_blob(self, obj: Any) -> None:
        pass

    async def store_vector(self, obj: Any) -> None:
        pass

    async def store_kv(self, obj: Any) -> None:
        pass

    async def store_graph(self, obj: Any) -> None:
        pass

import json

import chromadb
import pandas as pd

from knwl.logging import log
from knwl.storage.vector_storage_base import VectorStorageBase
from knwl.utils import get_full_path


class ChromaStorage(VectorStorageBase):
    """
    Straightforward vector storage based on ChromaDB.
    The embedding is the default all-MiniLM-L6-v2, which is a 384-dimensional embedding.
    This is a shallow embedding, so it is not suitable for all purposes.

    The `metadata` parameter allows you to specify additional metadata fields to store with each document.
    Only the metadata fields specified in the `metadata` list will be stored with the documents.
    """

    metadata: list[str]

    def __init__(
        self,
        collection_name: str = "default",
        metadata=None,
        memory: bool = False,
        path: str = "$test/vector",
    ):
        super().__init__()
        self._in_memory = memory
        self._metadata = metadata or []
        self._collection_name = collection_name
        self._path = path
        if self._path is not None and "." in self._path.split("/")[-1]:
            log.warn(
                f"The Chroma path '{self._path}' contains a '.' but should be a directory, not a file."
            )
        if not self._in_memory and self._path is not None:
            self._path = get_full_path(self._path)
            self.client = chromadb.PersistentClient(path=self._path)

        else:
            self.client = chromadb.Client()

        self.collection = self.client.get_or_create_collection(
            name=self._collection_name
        )

    @property
    def metadata(self):
        return self._metadata

    @property
    def collection_name(self):
        return self._collection_name

    @property
    def path(self):
        return self._path

    @property
    def in_memory(self):
        return self._in_memory

    async def query(self, query: str, top_k: int = 1) -> list[dict]:
        # ====================================================================================
        # Note that Chroma has auto-embedding based on all-MiniLM-L6-v2, so you don't need to provide embeddings.
        # The `query_texts` is auto=transformed using this model. The embedding dimension is only 384, so it really is rather shallow for most purposes.
        # ====================================================================================

        if not isinstance(query, str):
            raise ValueError(
                "Query must be a string. If you have a model, use model_dump_json() first."
            )
        if len(self._metadata) > 0:
            found = self.collection.query(
                query_texts=query, n_results=top_k, include=["documents", "metadatas"]
            )
        else:
            found = self.collection.query(
                query_texts=query, n_results=top_k, include=["documents"]
            )
        if found is None:
            return []
        coll = []
        for item in found["documents"][0]:
            coll.append(json.loads(item))
        return coll

    async def upsert(self, data: dict[str, dict]):
        if data is None or len(data) == 0:
            return data

        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                str_value = json.dumps(value)
            else:
                str_value = value
            embedding = None
            if "embedding" in value:
                embedding = value["embedding"]
            if "embeddings" in value:
                embedding = value["embeddings"]
            if len(self._metadata) > 0:
                metadata = {k: value.get(k, None) for k in self._metadata}
                self.collection.upsert(
                    ids=key,
                    documents=str_value,
                    metadatas=metadata,
                    embeddings=embedding,
                )
            else:
                self.collection.upsert(
                    ids=key, documents=str_value, embeddings=embedding
                )
        return data

    async def clear(self):
        self.client.delete_collection(self._collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self._collection_name
        )

    async def count(self):
        return self.collection.count()

    async def get_ids(self):
        ids_only_result = self.collection.get(include=[])
        return ids_only_result["ids"]

    async def to_dataframe(self) -> pd.DataFrame:
        data = self.collection.get(include=["documents", "metadatas", "embeddings"])
        documents = [json.loads(doc) for doc in data["documents"]]
        metadatas = data["metadatas"]
        df = pd.DataFrame(documents)
        if metadatas:
            meta_df = pd.DataFrame(metadatas)
            df = pd.concat([df, meta_df], axis=1)
        return df

    async def save(self):
        # happens automatically
        pass

    async def get_by_id(self, id: str):
        result = self.collection.get(ids=[id], include=["documents", "metadatas"])
        if result["documents"]:
            return json.loads(result["documents"][0])
        return None

    async def get_collection_names(self):
        return [col.name for col in self.client.list_collections()]

    def __repr__(self):
        return f"ChromaStorage, collection={self._collection_name}, path={self._path}, memory={self._in_memory}, metadata={self._metadata})"

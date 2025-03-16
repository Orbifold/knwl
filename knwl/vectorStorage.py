import json
import os

import chromadb
import pandas as pd

from knwl.settings import settings
from knwl.models.StorageNameSpace import StorageNameSpace


class VectorStorage(StorageNameSpace):
    metadata: list[str]

    def __init__(self, namespace: str = "default", metadata=None, caching: bool = False):
        super().__init__(namespace, caching)
        if metadata is None:
            metadata = []
        self.metadata = metadata

        if self.caching:
            self.client = chromadb.PersistentClient(path=os.path.join(settings.working_dir, f"vectordb_{self.namespace}"))
        else:
            self.client = chromadb.Client()

        self.collection = self.client.get_or_create_collection(name=self.namespace)

    async def query(self, query: str, top_k: int = 1) -> list[dict]:
        if len(self.metadata) > 0:
            found = self.collection.query(query_texts=query, n_results=top_k, include=["documents", "metadatas"])
        else:
            found = self.collection.query(query_texts=query, n_results=top_k, include=["documents"])
        if found is None:
            return []
        coll = []
        for item in found["documents"][0]:
            coll.append(json.loads(item))
        return coll

    async def upsert(self, data: dict[str, dict]):
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                str_value = json.dumps(value)
            else:
                str_value = value
            if len(self.metadata) > 0:
                metadata = {k: value.get(k, None) for k in self.metadata}
                self.collection.upsert(ids=key, documents=str_value, metadatas=metadata)
            else:
                self.collection.upsert(ids=key, documents=str_value)
        return data

    async def clear(self):
        self.client.delete_collection(self.namespace)
        self.collection = self.client.get_or_create_collection(name=self.namespace)

    async def count(self):
        return self.collection.count()

    async def get_ids(self):
        ids_only_result = self.collection.get(include=[])
        return ids_only_result['ids']

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

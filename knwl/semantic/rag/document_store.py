from torch import StorageBase
from knwl.di import defaults
from knwl.models.KnwlDocument import KnwlDocument
from knwl.semantic.rag.document_base import DocumentBase
from knwl.storage.storage_adapter import StorageAdapter


@defaults("document_store")
class DocumentStore(DocumentBase):
    """
    Default implementation of DocumentBase.
    This only CRUDs documents to/from storage, if you want auto-chunking and embeddings,
    use the `RagStore` instead.
    """

    def __init__(
        self,
        document_storage: StorageBase | None = None,
    ):
        super().__init__()
        self.document_storage: StorageBase = document_storage
        if self.document_storage is None:
            raise ValueError(f"DocumentStore: document_storage is required.")

    async def upsert(self, obj: str | KnwlDocument) -> str:
        if isinstance(obj, str):
            document = KnwlDocument(content=str(obj).strip())
        else:
            document = obj

        await StorageAdapter.upsert(document, self.document_storage)
        return document.id

    async def get_by_id(self, document_id: str) -> KnwlDocument | None:
        found = await self.document_storage.get_by_id(document_id)
        if found is None:
            return None
        elif isinstance(found, KnwlDocument):
            return found
        else:
            return KnwlDocument.model_validate(found)

    async def delete_by_id(self, document_id: str) -> None:
        await self.document_storage.delete_by_id(document_id)

    async def exists(self, document_id: str) -> bool:
        return await self.document_storage.exists(document_id)

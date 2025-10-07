from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase


class EntityExtractionBase(FrameworkBase, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)

       

    @abstractmethod
    async def extract(
        self, text: str, entities: list[str] = None, chunk_id: str = None
    ) -> dict | None:
        pass

    @abstractmethod
    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        pass

    @abstractmethod
    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        pass
from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models import KnwlEntity
from knwl.utils import hash_with_prefix

class EntityExtractionBase(FrameworkBase, ABC):
    """
    Abstract base class for entity extraction implementations.
   
    Args:
        *args: Variable length argument list passed to parent class.
        **kwargs: Arbitrary keyword arguments passed to parent class.
            override: Optional configuration override dictionary.
    Methods:
        extract: Extract entities from text and return as dictionary.
        extract_records: Extract entities from text and return as list of records.
        extract_json: Extract entities from text and return as JSON dictionary.
    Note:
        This is an abstract base class and cannot be instantiated directly.
        All abstract methods must be implemented by subclasses.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

       

    @abstractmethod
    async def extract(
        self, text: str, entities: list[str] = None, chunk_id: str = None
    ) -> list[KnwlEntity] | None:
        pass

    @abstractmethod
    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        pass

    @abstractmethod
    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        pass
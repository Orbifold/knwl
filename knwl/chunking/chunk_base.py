import os
from pathlib import Path
from abc import ABC, abstractmethod
from graspologic import List

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk


class ChunkBase(FrameworkBase):
    """
    Base class for diverse chunking implementations.
    This class defines the interface and common properties for chunking systems.
    """

    @abstractmethod
    async def chunk(self, content: str, source_key: str = None) -> List[KnwlChunk]:
        """
        Chunk the content into smaller pieces.

        Args:
            content (str): The content to be chunked.
            source_key (str, optional): The key of the source document.
        Returns:
            List[KnwlChunk]: A list of Chunk objects, each containing a portion of the content.
        """
        pass

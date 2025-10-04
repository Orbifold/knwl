import os
from pathlib import Path
from abc import ABC, abstractmethod
from graspologic import List

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk


class SummarizationBase(FrameworkBase):

    @abstractmethod
    async def summarize(self, content: str | list[str]) -> str:
        pass

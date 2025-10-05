import os
from pathlib import Path
from abc import ABC, abstractmethod
from graspologic import List

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk


class SummarizationBase(FrameworkBase):

    @abstractmethod
    async def summarize(
        self, content: str | list[str], entity_or_relation_name: str|list[str] = None
    ) -> str:
        pass

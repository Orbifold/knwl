import os
from pathlib import Path
from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk


class SummarizationBase(FrameworkBase):

    @abstractmethod
    async def summarize(
        self, content: str | list[str], entity_or_relation_name: str|list[str] = None
    ) -> str:
        """
        Summarize the given content.
        Args:
            content: str | list[str]: The content to summarize.
            entity_or_relation_name:  str | list[str]: The name of the entity or relation to use for the summary.

        Returns:
            str: The summarized content.

        """
        pass

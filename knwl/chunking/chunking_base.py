import os
from pathlib import Path
from abc import ABC, abstractmethod

from knwl.framework_base import FrameworkBase
from knwl.models.KnwlChunk import KnwlChunk


class ChunkingBase(FrameworkBase):
    """
    Base class for diverse chunking implementations.
    This class defines the interface and common properties for chunking systems.
    """

    @abstractmethod
    async def chunk(self, content: str, source_key: str = None) -> list[KnwlChunk]:
        """
        Chunk the content into smaller pieces.

        Args:
            content (str): The content to be chunked.
            source_key (str, optional): The key of the source document.
        Returns:
            list[KnwlChunk]: A list of Chunk objects, each containing a portion of the content.
        """
        ...

    @abstractmethod
    async def encode(self, content: str) -> list[int]:
        """
        Encodes a given string using the tiktoken library based on the specified model.
        Args:
            content (str): The string content to be encoded.
            settings.tokenize_model (str, optional): The name of the model to use for encoding. Defaults to "gpt-4o".
        Returns:
            list[int]: A list of token IDs representing the encoded string.
        """
        ...

    @abstractmethod
    async def decode(self, tokens: list[int]) -> str:
        """
        Decodes a list of tokens into a string using the specified model's encoding.

        Args:
            tokens (list[int]): A list of integer tokens to be decoded.
            settings.tokenize_model (str, optional): The name of the model to use for decoding. Defaults to "gpt-4o".

        Returns:
            str: The decoded string content.
        """
        ...

    @abstractmethod
    async def count_tokens(self, content: str) -> int:
        """
        Counts the number of tokens in the given content.
        Args:
            content (str): The content to be tokenized.
        Returns:
            int: The number of tokens in the content.
        """
        ...

    @abstractmethod
    async def truncate_content(self, content: str, max_token_size: int) -> str:
        """
        Truncate a list of data based on the token size limit.
        This function iterates over the given list and accumulates the token size
        of each element (after applying the key function and encoding). It stops
        and returns a truncated list when the accumulated token size exceeds the
        specified maximum token size.
        Args:
            content (list): The list of data to be truncated.
            max_token_size (int): The maximum allowed token size for the truncated list.
        Returns:
            list: A truncated list where the total token size does not exceed the
                specified maximum token size.
        """
        ...

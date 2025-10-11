from typing import List

from chromadb import get_settings
from knwl.chunking.chunk_base import ChunkBase
from knwl.models.KnwlChunk import KnwlChunk
import tiktoken


class TiktokenChunking(ChunkBase):
    """
    Chunking implementation using tiktoken for token-based chunking.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self.model = self.get_param(
            ["chunking", "tiktoken", "model"],
            args,
            kwargs,
            default="gpt-4o-mini",
            override=config,
        )
        self.chunk_size = self.get_param(
            ["chunking", "tiktoken", "size"],
            args,
            kwargs,
            default=1024,
            override=config,
        )
        self.chunk_overlap = self.get_param(
            ["chunking", "tiktoken", "overlap"],
            args,
            kwargs,
            default=128,
            override=config,
        )
        self.ENCODER = None

    def encode(self, content: str) -> list[int]:
        """
        Encodes a given string using the tiktoken library based on the specified model.
        Args:
            content (str): The string content to be encoded.
            settings.tokenize_model (str, optional): The name of the model to use for encoding. Defaults to "gpt-4o".
        Returns:
            List[int]: A list of token IDs representing the encoded string.
        """
        self.ensure_encoder()
        tokens = self.ENCODER.encode(content)
        return tokens

    def decode(self, tokens: list[int]) -> str:
        """
        Decodes a list of tokens into a string using the specified model's encoding.

        Args:
            tokens (list[int]): A list of integer tokens to be decoded.
            settings.tokenize_model (str, optional): The name of the model to use for decoding. Defaults to "gpt-4o".

        Returns:
            str: The decoded string content.
        """
        self.ensure_encoder()
        content = self.ENCODER.decode(tokens)
        return content

    def ensure_encoder(self):
        if self.ENCODER is None:
            self.ENCODER = tiktoken.encoding_for_model(self.model)

    async def chunk(self, content: str, source_key: str = None) -> List[KnwlChunk]:
        tokens = self.encode(content)
        results = []
        for index, start in enumerate(
            range(0, len(tokens), self.chunk_size - self.chunk_overlap)
        ):
            chunk_content = self.decode(tokens[start : start + self.chunk_size])
            if len(chunk_content.strip()) > 0:
                results.append(
                    KnwlChunk(
                        content=chunk_content.strip(),
                        tokens=min(self.chunk_size, len(tokens) - start),
                        index=index,
                        origin_id=source_key,
                    )
                )
        return results

    def count_tokens(self, content: str) -> int:
        """
        Counts the number of tokens in the given content.
        Args:
            content (str): The content to be tokenized.
        Returns:
            int: The number of tokens in the content.
        """
        if content is None or len(content.strip()) == 0:
            return 0
        return len(self.encode(str.strip(content)))

    def truncate_content(self, content: str, max_token_size: int) -> str:
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

        if max_token_size <= 0:
            return ""
        tokens = self.encode(content)
        if len(tokens) <= max_token_size:
            return content
        else:
            return self.decode(tokens[:max_token_size])

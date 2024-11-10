from typing import List

import tiktoken
from .settings import settings
from .utils import KnwlChunk

ENCODER = None


def encode(content: str):
    """
    Encodes a given string using the tiktoken library based on the specified model.
    Args:
        content (str): The string content to be encoded.
        settings.tokenize_model (str, optional): The name of the model to use for encoding. Defaults to "gpt-4o".
    Returns:
        List[int]: A list of token IDs representing the encoded string.
    """
    global ENCODER
    if ENCODER is None:
        ENCODER = tiktoken.encoding_for_model(settings.tokenize_model)
    tokens = ENCODER.encode(content)
    return tokens


def decode(tokens: list[int]):
    """
    Decodes a list of tokens into a string using the specified model's encoding.

    Args:
        tokens (list[int]): A list of integer tokens to be decoded.
        settings.tokenize_model (str, optional): The name of the model to use for decoding. Defaults to "gpt-4o".

    Returns:
        str: The decoded string content.
    """
    global ENCODER
    if ENCODER is None:
        ENCODER = tiktoken.encoding_for_model(settings.tokenize_model)
    content = ENCODER.decode(tokens)
    return content


def chunk(content: str, source_key: str = None) -> List[KnwlChunk]:
    """
    Splits the given content into chunks based on tokenization settings.
    Args:
        content (str): The content to be chunked.
        source_key (str, optional): The key of the source document.
    Returns:
        List[KnwlChunk]: A list of Chunk objects, each containing a portion of the content.
    """

    tokens = encode(content)
    results = []
    for index, start in enumerate(range(0, len(tokens), settings.tokenize_size - settings.tokenize_overlap)):
        chunk_content = decode(tokens[start: start + settings.tokenize_size])
        if len(chunk_content.strip()) > 0:
            results.append(KnwlChunk(content=chunk_content.strip(), tokens=min(settings.tokenize_size, len(tokens) - start), index=index, originId=source_key))
    return results


def truncate_list_by_token_size(list_data: list, key: callable, max_token_size: int):
    """
    Truncate a list of data based on the token size limit.
    This function iterates over the given list and accumulates the token size
    of each element (after applying the key function and encoding). It stops
    and returns a truncated list when the accumulated token size exceeds the
    specified maximum token size.
    Args:
        list_data (list): The list of data to be truncated.
        key (callable): A function that extracts the relevant data from each element
                        in the list for token size calculation.
        max_token_size (int): The maximum allowed token size for the truncated list.
    Returns:
        list: A truncated list where the total token size does not exceed the
              specified maximum token size.
    """

    if max_token_size <= 0:
        return []
    tokens = 0
    for i, data in enumerate(list_data):
        tokens += len(encode(key(data)))
        if tokens > max_token_size:
            return list_data[:i]
    return list_data

import pytest

from knwl.settings import settings
from knwl.tokenize import (
    encode,
    decode,
    chunk,
    truncate_content,
)
from knwl.utils import KnwlChunk


def test_encode_string_by_tiktoken():
    content = "Hello, world!"
    tokens = encode(content)
    assert isinstance(tokens, list)
    assert all(isinstance(token, int) for token in tokens)


def test_decode_tokens_by_tiktoken():
    content = "Hello, world!"
    tokens = encode(content)
    decoded_content = decode(tokens)
    assert decoded_content == content


def test_chunking_by_token_size():
    content = (
        "This is a test content to be chunked into smaller pieces based on token size."
    )
    chunks = chunk(content)
    assert isinstance(chunks, list)
    assert all(isinstance(c, KnwlChunk) for c in chunks)
    assert all(c.tokens>0 for c in chunks)
    assert all(c.content is not None for c in chunks)


def test_chunking_by_token_size_with_overlap():
    content = (
        "This is a test content to be chunked into smaller pieces based on token size."
    )
    settings.update(tokenize_size=10, tokenize_overlap=2)
    chunks = chunk(content)
    assert len(chunks) > 1
    assert chunks[0].content in content
    assert chunks[1].content in content


def test_chunking_by_token_size_large_content():
    content = "This is a test content " * 1000
    chunks = chunk(content)
    assert len(chunks) > 1
    assert chunks[0].content in content
    assert chunks[-1].content in content


def test_truncate_list_by_token_size():
    list_data = ["This is a test.", "Another test.", "Yet another test."]
    def key(x): return x
    max_token_size = 10
    truncated_list = truncate_content(
        list_data, key, max_token_size)
    assert isinstance(truncated_list, list)
    assert len(truncated_list) <= len(list_data)


def test_truncate_list_by_token_size_with_zero_max_token_size():
    list_data = ["This is a test.", "Another test.", "Yet another test."]
    def key(x): return x
    max_token_size = 0
    truncated_list = truncate_content(
        list_data, key, max_token_size)
    assert truncated_list == []


def test_truncate_list_by_token_size_with_large_max_token_size():
    list_data = ["This is a test.", "Another test.", "Yet another test."]
    def key(x): return x
    max_token_size = 1000
    truncated_list = truncate_content(
        list_data, key, max_token_size)
    assert truncated_list == list_data


def test_truncate_list_by_token_size_with_exact_max_token_size():
    list_data = ["This is a test.", "Another test.", "Yet another test."]
    def key(x): return x
    max_token_size = len(encode("This is a test.")) + \
        len(encode("Another test."))
    truncated_list = truncate_content(
        list_data, key, max_token_size)
    assert len(truncated_list) == 2
    assert truncated_list == list_data[:2]

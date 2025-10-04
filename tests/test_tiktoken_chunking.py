import pytest
from knwl.chunking import TiktokenChunking
from knwl.models.KnwlChunk import KnwlChunk

chunker = TiktokenChunking()


def test_encode_string():
    content = "Hello, world!"
    tokens = chunker.encode(content)
    assert isinstance(tokens, list)
    assert all(isinstance(token, int) for token in tokens)


# def test_decode_tokens_by_tiktoken():
#     content = "Hello, world!"
#     tokens = encode(content)
#     decoded_content = decode(tokens)
#     assert decoded_content == content


# def test_chunking_by_token_size():
#     content = (
#         "This is a test content to be chunked into smaller pieces based on token size."
#     )
#     chunks = chunk(content)
#     assert isinstance(chunks, list)
#     assert all(isinstance(c, KnwlChunk) for c in chunks)
#     assert all(c.tokens > 0 for c in chunks)
#     assert all(c.content is not None for c in chunks)


# def test_chunking_by_token_size_with_overlap():
#     content = (
#         "This is a test content to be chunked into smaller pieces based on token size."
#     )
#     settings.update(tokenize_size=10, tokenize_overlap=2)
#     chunks = chunk(content)
#     assert len(chunks) > 1
#     assert chunks[0].content in content
#     assert chunks[1].content in content


# def test_chunking_by_token_size_large_content():
#     content = "This is a test content " * 1000
#     chunks = chunk(content)
#     assert len(chunks) > 1
#     assert chunks[0].content in content
#     assert chunks[-1].content in content

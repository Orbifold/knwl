import pytest

from knwl.chunking import TiktokenChunking
from knwl.models.KnwlChunk import KnwlChunk

from knwl.services import services


def test_encode_string():
    chunker = TiktokenChunking()
    content = "Hello, world!"
    tokens = chunker.encode(content)
    assert isinstance(tokens, list)
    assert all(isinstance(token, int) for token in tokens)


def test_decode_tokens():
    chunker = TiktokenChunking()
    content = "Hello, world!"
    tokens = chunker.encode(content)
    decoded_content = chunker.decode(tokens)
    assert decoded_content == content


@pytest.mark.asyncio
async def test_chunking():
    chunker = TiktokenChunking(size=10, overlap=2)
    content = "This is a test content to be chunked into smaller pieces based on token size. You can adjust the chunk size and overlap as needed."
    chunks = await chunker.chunk(content)
    assert isinstance(chunks, list)
    assert all(isinstance(c, KnwlChunk) for c in chunks)
    assert all(c.tokens > 0 for c in chunks)
    assert all(c.content is not None for c in chunks)
    assert len(chunks) > 1
    assert chunks[0].content in content
    assert chunks[1].content in content
    for chunk in chunks:
        print(f"Chunk (tokens: {chunk.tokens}): {chunk.content}")


def test_count_tokens():
    chunker = TiktokenChunking()
    content = "Hello, world!"
    token_count = chunker.count_tokens(content)
    assert isinstance(token_count, int)
    assert token_count > 0
    assert token_count == len(chunker.encode(content))


def test_decode_tokens_by_tiktoken():
    chunker = TiktokenChunking()
    content = "Hello, world!"
    tokens = chunker.encode(content)
    decoded_content = chunker.decode(tokens)
    assert decoded_content == content


@pytest.mark.asyncio
async def test_chunking_by_token_size():
    chunker = TiktokenChunking(size=10, overlap=0)
    content = (
        "This is a test content to be chunked into smaller pieces based on token size."
    )
    chunks = await chunker.chunk(content)
    assert len(chunks) > 1
    assert chunks[0].content in content
    assert chunks[1].content in content


@pytest.mark.asyncio
async def test_via_services():
    chunker = services.get_default_service("chunking")
    assert isinstance(chunker, TiktokenChunking)
    assert chunker.chunk_size == 1024
    assert chunker.chunk_overlap == 128

    def create_class_from_dict(name, data):
        return type(name, (), data)

    async def chunk(self, *args, **kwargs):
        return [KnwlChunk(content="special chunk", tokens=10, index=0)]

    SpecialClass = create_class_from_dict("Special", {"name": "Swa", "chunk": chunk})

    config_override = {
        "chunking": {"default": "special", "special": {"class": SpecialClass()}}
    }
    chunker = services.get_default_service("chunking", override=config_override)
    assert chunker.name == "Swa"
    chunks = await chunker.chunk("Anything")
    assert len(chunks) == 1
    assert chunks[0].content == "special chunk"

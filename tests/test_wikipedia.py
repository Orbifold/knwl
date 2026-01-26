import pytest

from knwl.collect.wikipedia import WikipediaCollector
from knwl.models import KnwlDocument


@pytest.mark.asyncio
async def test_fetch_wikipedia_article():
    page_title = "Python (programming language)"
    document = await WikipediaCollector.fetch_article(page_title)

    assert document is not None, "Failed to fetch the Wikipedia article."
    assert isinstance(document, KnwlDocument), "Returned object is not a KnwlDocument."
    assert (
        page_title in document.name
    ), "Document name does not match the requested page title."
    assert len(document.content) > 0, "Document content is empty."
    assert len(document.description) > 0, "Document description is empty."
    assert document.id is not None, "Document ID is None."


@pytest.mark.asyncio
async def test_fetch_nonexistent_wikipedia_article():
    page_title = "ThisPageDoesNotExist1234567890"
    document = await WikipediaCollector.fetch_article(page_title)

    assert document is None, "Expected None for a nonexistent Wikipedia article."

@pytest.mark.asyncio
async def test_get_random_library_article():
    document = await WikipediaCollector.get_random_library_article("mathematics")

    assert document is not None, "Failed to fetch a random library article."
    assert isinstance(document, KnwlDocument), "Returned object is not a KnwlDocument."
    assert len(document.content) > 0, "Document content is empty."
    assert len(document.description) > 0, "Document description is empty."
    assert document.id is not None, "Document ID is None."
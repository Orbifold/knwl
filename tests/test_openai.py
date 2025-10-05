import pytest
from faker import Faker


from knwl.llm.openai import OpenAIClient
from knwl.models.KnwlLLMAnswer import KnwlLLMAnswer
from knwl.utils import get_full_path

fake = Faker()


@pytest.mark.asyncio
async def test_basic_ask():
    """
    Test basic functionality of OpenAIClient.

    Tests the following:
    - Default model and temperature initialization
    - Custom model and temperature initialization
    - Basic ask functionality with response validation
    - Caching behavior after making a request

    The test verifies that the OpenAIClient properly initializes with both
    default and custom parameters, successfully processes a simple query,
    returns a valid KnwlLLMAnswer response, and correctly caches the query.
    """
    llm = OpenAIClient()
    assert llm.model == "gpt-4o-mini"
    assert llm.temperature == 0.1

    llm = OpenAIClient(model="gpt-4.1", temperature=0.5)
    assert llm.model == "gpt-4.1"
    assert llm.temperature == 0.5

    # let's change the default caching path
    # note that only the overrides are passed, the rest is taken from default_config
    file_name = fake.word()
    config = {"llm_caching": {"json": {"path": f"$test/{file_name}.json"}}}
    llm = OpenAIClient(caching="json", override=config)
    resp = await llm.ask("Hello")
    assert resp is not None
    assert isinstance(resp, KnwlLLMAnswer)

    assert await llm.is_cached("Hello") is True
    file_path = get_full_path(f"$test/{file_name}.json")
    import os

    assert os.path.exists(file_path)
    print("")
    print(resp.answer)


@pytest.mark.asyncio
async def test_override_caching():
    """
    Test that OpenAIClient correctly overrides the default caching service with a custom one.

    This test verifies that:
    1. A custom caching class can be dynamically created and configured
    2. The OpenAIClient accepts the custom caching configuration through override parameter
    3. The custom caching service is properly instantiated and accessible
    4. Custom caching methods are correctly called when cache operations are performed
    5. The caching service maintains its custom attributes (like 'name')

    The test creates a mock caching class with a custom 'is_in_cache' method that sets a flag
    when called, allowing verification that the custom caching logic is actually being used.
    """

    def create_class_from_dict(name, data):
        return type(name, (), data)

    passed_through_cache = False

    async def is_in_cache(self, *args, **kwargs):
        nonlocal passed_through_cache
        passed_through_cache = True
        return True

    SpecialClass = create_class_from_dict(
        "Special", {"name": "Swa", "is_in_cache": is_in_cache}
    )

    config = {
        "llm": {"ollama": {"caching": "special"}},
        "llm_caching": {"special": {"class": SpecialClass()}},
    }
    llm = OpenAIClient(override=config)
    assert llm.caching_service is not None
    assert llm.caching_service.name == "Swa"
    assert await llm.is_cached("Anything") is True
    assert passed_through_cache is True


@pytest.mark.asyncio
async def test_no_cache():
    """
    Test that OpenAI client works correctly when caching is disabled.

    Verifies that:
    - The caching service is None when caching is disabled
    - Messages are not cached when caching is disabled
    - The is_cached method returns False for any message when caching is disabled
    """
    llm = OpenAIClient(caching=None)
    assert llm.caching_service is None
    await llm.ask("Hello")
    assert await llm.is_cached("Hello") is False

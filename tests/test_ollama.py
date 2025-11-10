from unittest.mock import patch
import pytest
from faker import Faker
import os
from knwl.config import get_config
from knwl.format import print_knwl
from knwl.services import services
from knwl.llm.ollama import OllamaClient
from knwl.models.KnwlAnswer import KnwlAnswer
from knwl.utils import get_full_path
from knwl.llm.llm_cache_base import LLMCacheBase

pytestmark = pytest.mark.llm

fake = Faker()


@pytest.mark.asyncio
async def test_basic_ask():
    """
    Test basic functionality of OllamaClient.

    Tests the following:
    - Default model and temperature initialization
    - Custom model and temperature initialization
    - Basic ask functionality with response validation
    - Caching behavior after making a request

    The test verifies that the OllamaClient properly initializes with both
    default and custom parameters, successfully processes a simple query,
    returns a valid KnwlLLMAnswer response, and correctly caches the query.
    """
    llm = OllamaClient()
    assert llm.model == get_config("llm/ollama/model")
    assert llm.temperature == get_config("llm/ollama/temperature")

    llm = OllamaClient(model="gemma3:4b", temperature=0.5)
    assert llm.model == "gemma3:4b"
    assert llm.temperature == 0.5

    # let's change the default caching path
    # note that only the overrides are passed, the rest is taken from default_config
    file_name = fake.word()
    config = {"llm_caching": {"user": {"path": f"$/tests/{file_name}.json"}}}
    llm = services.get_service("llm", "ollama", override=config)
    resp = await llm.ask("Hello")
    assert resp is not None
    assert isinstance(resp, KnwlAnswer)

    assert await llm.is_cached("Hello") is True
    file_path = get_full_path(f"$/tests/{file_name}.json")
    assert os.path.exists(file_path)
    print("")
    print(resp.answer)


@pytest.mark.asyncio
async def test_override_caching():
    """
    Test that OllamaClient correctly overrides the default caching service with a custom one.

    This test verifies that:
    1. A custom caching class can be dynamically created and configured
    2. The OllamaClient accepts the custom caching configuration through override parameter
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
        "llm": {"ollama": {"caching_service": "@/llm_caching/special"}},
        "llm_caching": {"special": {"class": SpecialClass()}},
    }
    with patch(
        "knwl.llm.ollama.OllamaClient.validate_params",
        return_value=None,
    ):
        llm = services.get_service("llm", "ollama", override=config)
        assert llm.caching_service is not None
        assert llm.caching_service.name == "Swa"
        assert await llm.is_cached("Anything") is True
        assert passed_through_cache is True


@pytest.mark.asyncio
async def test_no_cache():
    # the following will not disable caching, since injection assumes none is set
    # llm = OllamaClient(caching_service=None)
    # assert llm.caching_service is not None
    config = {
        "llm": {"ollama": {"caching_service": "None"}},
    }
    llm = services.get_service("llm", "ollama", override=config)
    await llm.ask("Hello")
    assert await llm.is_cached("Hello") is False

    a = await llm.ask(None)
    assert a is None
    a = await llm.ask("")
    assert a is None

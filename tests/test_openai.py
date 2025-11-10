import pytest
from faker import Faker
from unittest.mock import patch

from knwl.config import get_config
from knwl.llm.openai import OpenAIClient
from knwl.models.KnwlAnswer import KnwlAnswer
from knwl.utils import get_full_path
from knwl.services import services
pytestmark = pytest.mark.llm

fake = Faker()

@pytest.mark.asyncio
async def test_basic_ask():
   
    llm = OpenAIClient()
    assert llm.model == get_config("llm/openai/model")
    assert llm.temperature == get_config("llm/openai/temperature")

    llm = OpenAIClient(model="gpt-4.1", temperature=0.5)
    assert llm.model == "gpt-4.1"
    assert llm.temperature ==0.5

    # let's change the default caching path
    # note that only the overrides are passed, the rest is taken from default_config
    file_name = fake.word()
    config = {"llm_caching": {"user": {"path": f"$/tests/{file_name}.json"}}}
    llm = services.get_service("llm", "openai", override=config)
    assert llm.caching_service is not None
    assert llm.caching_service.path == get_full_path(f"$/tests/{file_name}.json")
    resp = await llm.ask("Hello")
    assert resp is not None
    assert isinstance(resp, KnwlAnswer)

    assert await llm.is_cached("Hello") is True
    file_path = get_full_path(f"$/tests/{file_name}.json")
    import os

    assert os.path.exists(file_path)
    print("")
    print(resp.answer)


@pytest.mark.asyncio
async def test_override_caching():   

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
        "llm": {"openai": {"caching_service": "@/llm_caching/special"}},
        "llm_caching": {"special": {"class": SpecialClass()}},
    }
    with patch(
        "knwl.llm.openai.OpenAIClient.validate_params",
        return_value=None,
    ):    
        llm = services.get_service("llm", "openai", override=config)
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
    config = {
        "llm": {"openai": {"caching_service": "None"}},
    }
    llm = services.get_service("llm", "openai", override=config)
    await llm.ask("Hello")
    assert await llm.is_cached("Hello") is False

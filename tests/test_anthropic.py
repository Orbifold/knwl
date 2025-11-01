import pytest
from faker import Faker


from knwl.llm.anthropic import AnthropicClient
from knwl.models.KnwlAnswer import KnwlAnswer
from knwl.utils import get_full_path
from knwl.services import services

pytestmark = pytest.mark.llm

fake = Faker()


@pytest.mark.asyncio
async def test_basic_ask():

    llm = AnthropicClient()

    # let's change the default caching path
    # note that only the overrides are passed, the rest is taken from default_config
    file_name = fake.word()
    config = {"llm_caching": {"user": {"path": f"$/tests/{file_name}.json"}}}
    llm = services.get_service("llm", "anthropic", override=config)
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

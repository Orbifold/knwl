import os

import pytest

from knwl.config import get_config
from knwl.llm.ollama import OllamaClient
from knwl.services import services
from knwl.utils import get_full_path

pytestmark = pytest.mark.llm


def test_get_spec():

    override_config = {
        "food": {
            "default": "pizza",
            "pizza": {"size": "large", "delivery": "transport/car"},
            "burger": {"size": "medium"},
        },
        "transport": {"car": {"wheels": 4}, "bike": {"wheels": 2}},
    }
    specs = services.get_service_specs("food", override=override_config)
    assert specs["service_name"] == "food"
    assert specs["variant_name"] == "pizza"
    assert specs["size"] == "large"
    with pytest.raises(ValueError):
        services.get_service_specs("unknown_service", override=override_config)
    with pytest.raises(ValueError):
        services.get_service_specs("food", "unknown_variant", override=override_config)

    specs = services.get_service_specs("food/burger", override=override_config)
    assert specs["service_name"] == "food"
    assert specs["variant_name"] == "burger"
    assert specs["size"] == "medium"

    specs = services.get_service_specs("food", "default", override=override_config)
    assert specs["service_name"] == "food"
    assert specs["variant_name"] == "pizza"
    specs = services.get_service_specs("food/default", None, override=override_config)
    assert specs["service_name"] == "food"
    assert specs["variant_name"] == "pizza"
    with pytest.raises(ValueError):
        services.get_service_specs(None, override=override_config)
    with pytest.raises(ValueError):
        # can't have both "/" and variant in one call
        services.get_service_specs("a/b", "c", override=override_config)

    


@pytest.mark.asyncio
async def test_service_simplicity():

    # simply getting the service with default config
    json_service_default = services.get_service("json")
    assert json_service_default.path == get_full_path(
        get_config("json", "basic", "path")
    )
    # it's a singleton
    json_service_default2 = services.get_service("json")
    assert json_service_default.id == json_service_default2.id

    # you can override the config to define a custom path
    json_service_custom = services.get_service(
        "json/custom",
        override={
            "json": {
                "custom": {
                    "class": "knwl.storage.json_storage.JsonStorage",
                    "path": "$/tests/custom.json",
                }
            }
        },
    )
    await json_service_custom.upsert({"key1": {"data": 123}})
    assert os.path.exists(get_full_path("$/tests/custom.json"))


def test_service_instantiation():
    assert services.get_service_specs("llm")
    assert services.get_default_variant_name("llm") == "ollama"
    llm_service = services.instantiate_service("llm")
    assert llm_service is not None
    assert llm_service.__class__.__name__ == "OllamaClient"
    assert llm_service.model == get_config("llm", "ollama", "model")
    assert llm_service.temperature == 0.1
    assert llm_service.context_window == 32768

    # Test with override configuration
    override_config = {
        "llm": {
            "default": "ollama",
            "ollama": {
                "model": "custom_model:1b",
                "temperature": 0.5,
                "context_window": 16384,
                "caching": "json",
            },
        },
        "llm_caching": {"json": {"path": "custom_llm.json"}},
    }
    llm_service_overridden = services.instantiate_service(
        "llm", override=override_config
    )
    assert llm_service_overridden.model == "custom_model:1b"
    assert llm_service_overridden.temperature == 0.5
    assert llm_service_overridden.context_window == 16384
    assert llm_service_overridden.service_config is not None
    assert llm_service_overridden.service_config["service_name"] == "llm"


def test_service_params():
    model_name = "abc"
    llm = OllamaClient(model=model_name)
    assert llm._model == model_name
    assert llm.temperature == get_config("llm", "ollama", "temperature")
    # kwargs specified
    model_name = "bcr"
    llm = OllamaClient(model=model_name)
    assert llm._model == model_name

    # using config defaults
    llm = OllamaClient()
    assert llm._model == get_config("llm", "ollama", "model")

    # override
    override_config = {
        "llm": {
            "ollama": {
                "model": "zero",
                "temperature": 0.3,
                "context_window": 8192,
            }
        }
    }
    llm = services.get_service("llm", override=override_config)
    assert llm._model == "zero"
    assert llm.temperature == 0.3


def test_service_singleton():
    services.clear_singletons()
    assert len(services.singletons) == 0

    llm1 = services.get_service("llm")
    llm2 = services.get_service("llm")
    assert llm1.id == llm2.id

    llm3 = services.get_service("llm", variant_name="ollama")
    assert llm1.id == llm3.id
    override_config = {
        "llm": {
            "ollama": {
                "model": "override_model:1b",
                "temperature": 0.3,
                "context_window": 8192,
            }
        }
    }
    llm4 = services.get_service("llm", override=override_config)
    llm5 = services.get_service("llm", override=override_config)
    # for k in services.singletons:

    assert llm4.id == llm5.id
    assert llm4.id != llm1.id

from knwl.config import get_config
from knwl.llm.ollama import OllamaClient


def test_service_instantiation():
    from knwl.services import Services

    services = Services()
    assert services.service_exists("llm")
    assert services.get_default_variant_name("llm") == "ollama"
    llm_service = services.instantiate_service("llm")
    assert llm_service is not None
    assert llm_service.__class__.__name__ == "OllamaClient"
    assert llm_service.model == "qwen2.5:14b"
    assert llm_service.temperature == 0.1
    assert llm_service.context_window == 32768

    # Test with override configuration
    override_config = {"llm": {"default": "ollama", "ollama": {"model": "custom_model:1b", "temperature": 0.5, "context_window": 16384, "caching": "json", }, }, "llm_caching": {"json": {"path": "custom_llm.json"}}, }
    llm_service_overridden = services.instantiate_service("llm", override=override_config)
    assert llm_service_overridden.model == "custom_model:1b"
    assert llm_service_overridden.temperature == 0.5
    assert llm_service_overridden.context_window == 16384
    assert llm_service_overridden.caching_service_name == "json"


def test_service_params():
    model_name = "abc"
    # arg is a dict
    llm = OllamaClient({"model": model_name})
    assert llm.model == model_name
    assert llm.temperature == get_config("llm", "ollama", "temperature")
    # kwargs specified
    model_name = "bcr"
    llm = OllamaClient(model=model_name)
    assert llm.model == model_name

    # using config defaults
    llm = OllamaClient()
    assert llm.model == get_config("llm", "ollama", "model")

    # override
    override_config = {
        "llm":{
            "ollama": {
                "model": "override_model:1b",
                "temperature": 0.3,
                "context_window": 8192,
            }
        }
    }
    llm = OllamaClient(override=override_config)
    assert llm.model == "override_model:1b"
    assert llm.temperature == 0.3


def test_service_singleton():
    from knwl.services import Services

    services = Services()
    llm1 = services.get_service("llm")
    llm2 = services.get_service("llm")
    assert llm1.id == llm2.id

    llm3 = services.get_service("llm", variant_name="ollama")
    assert llm1.id == llm3.id

    override_config = {
        "llm":{
            "ollama": {
                "model": "override_model:1b",
                "temperature": 0.3,
                "context_window": 8192,
            }
        }
    }
    llm4 = services.get_service("llm", override=override_config)
    llm5 = services.get_service("llm", override=override_config)
    assert llm4.id == llm5.id
    assert llm4.id != llm1.id
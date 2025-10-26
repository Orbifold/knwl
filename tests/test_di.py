"""
Test suite for the dependency injection system.
"""

import pytest
from unittest.mock import Mock, patch
from knwl.di import (
    service,
    singleton_service,
    inject_config,
    defaults,
    inject_services,
    auto_inject,
    ServiceProvider,
    container,
)

pytestmark = pytest.mark.basic


class TestDependencyInjection:
    """
    Test cases for the dependency injection decorators and functionality.
    """

    def setup_method(self):
        """Clean up DI container before each test."""
        container._service_registry.clear()
        container._config_registry.clear()
        container._defaults_registry.clear()

    def test_fail_to_inject_service(self):
        """Test behavior when service creation fails."""
        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.side_effect = Exception("Service not found")

            @service("non_existent_service")
            def test_function(svc=None):
                return svc

            with pytest.raises(Exception, match="Service not found"):
                test_function()

            mock_services.create_service.assert_called_once_with(
                "non_existent_service", variant_name=None, override=None
            )

    def test_no_config(self):
        """Test behavior when no configuration is present."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.return_value = None

            @inject_config("non.existent.key")
            def test_function(key=None):
                return key

            result = test_function()
            assert result is None
            mock_get_config.assert_called_once_with("non", "existent", "key")

    def test_service_decorator_basic(self):
        """Test basic service injection."""
        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            @service("llm")
            def test_function(text: str, llm=None):
                print("Inside test_function")
                return llm.process(text)

            result = test_function("test text")

            mock_services.create_service.assert_called_once_with(
                "llm", variant_name=None, override=None
            )
            mock_service.process.assert_called_once_with("test text")

    def test_service_decorator_with_variant(self):
        """Test service injection with variant specification."""
        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            @service("llm", variant="ollama", param_name="abc")
            def test_function(text: str, abc=None):
                return abc.generate(text)

            result = test_function("test text")

            mock_services.create_service.assert_called_once_with(
                "llm", variant_name="ollama", override=None
            )
            mock_service.generate.assert_called_once_with("test text")

    def test_singleton_service_decorator(self):
        """Test singleton service injection."""
        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.get_service.return_value = mock_service

            @singleton_service("graph", variant="nx")
            def test_function(data: dict, graph=None):
                return graph.add_node(data)

            result = test_function({"id": "1", "name": "test"})

            mock_services.get_service.assert_called_once_with(
                "graph", variant_name="nx", override=None
            )
            mock_service.add_node.assert_called_once_with({"id": "1", "name": "test"})

    def test_inject_config_decorator(self):
        """Test configuration value injection."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "host"): "localhost",
                ("api", "port"): 8080,
            }.get(keys, None)

            @inject_config("api.host", "api.port")
            def test_function(host=None, port=None):
                return f"Server: {host}:{port}"

            result = test_function()

            assert result == "Server: localhost:8080"
            assert mock_get_config.call_count == 2

    def test_inject_services_decorator(self):
        """Test multiple service injection with inject_services."""
        mock_llm = Mock()
        mock_vector = Mock()

        with patch("knwl.di.services") as mock_services:

            def side_effect(service_name, variant_name=None, override=None):
                if service_name == "llm":
                    return mock_llm
                elif service_name == "vector":
                    return mock_vector
                return Mock()

            mock_services.create_service.side_effect = side_effect
            mock_services.get_service.side_effect = side_effect

            @inject_services(
                llm="llm",
                storage=("vector", "chroma"),
                graph={"service": "graph", "variant": "nx", "singleton": True},
            )
            def test_function(data: str, llm=None, storage=None, graph=None):
                return {
                    "llm_result": llm.process(data),
                    "storage_result": storage.store(data),
                    "graph_nodes": graph.number_of_nodes(),
                }

            result = test_function("test data")

            # Verify services were called correctly
            mock_llm.process.assert_called_once_with("test data")
            mock_vector.store.assert_called_once_with("test data")

    def test_auto_inject_decorator(self):
        """Test automatic injection based on parameter names."""
        mock_llm = Mock()
        mock_vector = Mock()

        with patch("knwl.di.services") as mock_services:

            def side_effect(service_name, variant_name=None, override=None):
                if service_name == "llm":
                    return mock_llm
                elif service_name == "vector":
                    return mock_vector
                return Mock()

            mock_services.get_service.side_effect = side_effect

            @auto_inject
            def test_function(text: str, llm=None, vector=None, other_param=None):
                results = {}
                if llm:
                    results["llm"] = llm.analyze(text)
                if vector:
                    results["vector"] = vector.search(text)
                return results

            result = test_function("test text")

            mock_llm.analyze.assert_called_once_with("test text")
            mock_vector.search.assert_called_once_with("test text")

    def test_service_provider_create_service(self):
        """Test ServiceProvider.create_service method."""
        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            service_instance = ServiceProvider.create_service("llm", variant="ollama")

            mock_services.create_service.assert_called_once_with(
                "llm", variant_name="ollama", override=None
            )
            assert service_instance == mock_service

    def test_service_provider_get_service(self):
        """Test ServiceProvider.get_service method."""
        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.get_service.return_value = mock_service

            service_instance = ServiceProvider.get_service("graph", variant="nx")

            mock_services.get_service.assert_called_once_with(
                "graph", variant_name="nx", override=None
            )
            assert service_instance == mock_service

    def test_service_provider_clear_singletons(self):
        """Test ServiceProvider.clear_singletons method."""
        with patch("knwl.di.services") as mock_services:
            ServiceProvider.clear_singletons()
            mock_services.clear_singletons.assert_called_once()

    def test_di_container_registration(self):
        """Test DI container service registration."""
        container.register_service_injection(
            "test_func", "llm", "ollama", "language_model", singleton=True
        )

        assert "test_func" in container._service_registry
        assert "language_model" in container._service_registry["test_func"]

        service_info = container._service_registry["test_func"]["language_model"]
        assert service_info["service_name"] == "llm"
        assert service_info["variant_name"] == "ollama"
        assert service_info["singleton"] is True

    def test_di_container_config_registration(self):
        """Test DI container config registration - verifies the registration mechanism."""
        container.register_config_injection("test_func", ["api.host", "api.port"])

        assert "test_func" in container._config_registry
        assert container._config_registry["test_func"]["config_keys"] == [
            "api.host",
            "api.port",
        ]
        assert container._config_registry["test_func"]["override"] is None

    def test_manual_config_injection_with_wrapper(self):
        """Test manual config registration with actual injection via wrapper."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "port"): 9000,
                ("api", "host"): "manual.host.com",
            }.get(keys, None)

            def my_function(host=None, port=None):
                return {"host": host, "port": port}

            # Manually register config injection
            func_name = f"{my_function.__module__}.{my_function.__qualname__}"
            container.register_config_injection(func_name, ["api.host", "api.port"])

            # To actually use manual registration, you need to manually call inject_dependencies
            injected_args = container.inject_dependencies(my_function)
            result = my_function(**injected_args)

            assert result == {"host": "manual.host.com", "port": 9000}
            assert mock_get_config.call_count == 2

    def test_config_injection_with_nested_keys(self):
        """Test config injection with deeply nested configuration keys."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("database", "connection", "host"): "db.example.com",
                ("database", "connection", "port"): 5432,
                ("logging", "level"): "INFO",
            }.get(keys, None)

            @inject_config(
                "database.connection.host", "database.connection.port", "logging.level"
            )
            def test_function(host=None, port=None, level=None):
                return {"db": f"{host}:{port}", "log_level": level}

            result = test_function()

            assert result == {"db": "db.example.com:5432", "log_level": "INFO"}
            assert mock_get_config.call_count == 3

    def test_config_injection_parameter_name_mapping(self):
        """Test that config keys are correctly mapped to parameter names."""
        container.register_config_injection(
            "test_func", ["api.server.host", "api.server.port"]
        )

        assert "test_func" in container._config_registry
        assert (
            "api.server.host" in container._config_registry["test_func"]["config_keys"]
        )
        assert (
            "api.server.port" in container._config_registry["test_func"]["config_keys"]
        )

    def test_config_injection_with_none_values(self):
        """Test config injection when config values are None."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.return_value = None

            @inject_config("missing.config.key")
            def test_function(key=None):
                return key

            result = test_function()
            assert result is None

    def test_config_injection_multiple_registrations(self):
        """Test multiple config registrations for the same function."""
        container.register_config_injection("func1", ["key1", "key2"])
        container.register_config_injection("func1", ["key3", "key4"])

        # Second registration should replace the first
        assert container._config_registry["func1"]["config_keys"] == ["key3", "key4"]

    def test_config_injection_empty_key_list(self):
        """Test config injection with empty key list."""
        container.register_config_injection("test_func", [])

        assert "test_func" in container._config_registry
        assert container._config_registry["test_func"]["config_keys"] == []

    def test_mixed_service_and_config_injection(self):
        """Test function with both service and config injection."""
        mock_service = Mock()

        with (
            patch("knwl.di.services") as mock_services,
            patch("knwl.di.get_config") as mock_get_config,
        ):

            mock_services.create_service.return_value = mock_service
            mock_get_config.side_effect = lambda *keys: {
                ("api", "timeout"): 30,
                ("api", "retries"): 3,
            }.get(keys, None)

            @service("llm")
            @inject_config("api.timeout", "api.retries")
            def test_function(text: str, llm=None, timeout=None, retries=None):
                return {
                    "result": llm.process(text),
                    "timeout": timeout,
                    "retries": retries,
                }

            result = test_function("test text")

            mock_services.create_service.assert_called_once()
            assert mock_get_config.call_count == 2
            assert result["timeout"] == 30
            assert result["retries"] == 3

    def test_config_injection_with_default_values(self):
        """Test that config injection respects function default values."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {("server", "port"): 8080}.get(
                keys, "default_value"
            )

            @inject_config("server.host", "server.port")
            def test_function(host="localhost", port=3000):
                return f"{host}:{port}"

            result = test_function()

            # Function defaults should be preserved (DI doesn't override defaults)
            assert result == "localhost:3000"

            # Config injection should only happen for None defaults
            @inject_config("server.host", "server.port")
            def test_function_with_none_defaults(host=None, port=None):
                return f"{host}:{port}"

            result2 = test_function_with_none_defaults()
            assert result2 == "default_value:8080"

    def test_config_injection_partial_override(self):
        """Test config injection when only some parameters are provided."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "host"): "configured.host.com"
            }.get(keys, None)

            @inject_config("api.host", "api.port")
            def test_function(host=None, port=None):
                return {"host": host, "port": port}

            # Pass port explicitly, should not be injected
            result = test_function(port=9000)

            assert result["host"] == "configured.host.com"
            assert result["port"] == 9000
            # Only host should be looked up in config
            mock_get_config.assert_called_once_with("api", "host")

    def test_config_injection_function_qualname_handling(self):
        """Test that function qualname is handled correctly for nested functions."""

        def outer_function():
            @inject_config("test.key")
            def inner_function(key=None):
                return key

            return inner_function

        inner_func = outer_function()
        func_name = f"{inner_func.__module__}.{inner_func.__qualname__}"

        # The function should be registered with the correct qualname
        assert func_name in container._config_registry

    def test_config_registry_independence(self):
        """Test that config registry is independent of service registry."""
        container.register_service_injection("func1", "service1")
        container.register_config_injection("func2", ["config.key1"])

        assert "func1" in container._service_registry
        assert "func2" in container._config_registry
        assert "func1" not in container._config_registry
        assert "func2" not in container._service_registry

    def test_parameter_override_prevents_injection(self):
        """Test that explicitly passed parameters prevent injection."""
        mock_service = Mock()
        user_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            @service("llm")
            def test_function(text: str, llm=None):
                return llm.process(text)

            # Pass explicit service - should not inject
            result = test_function("test text", llm=user_service)

            # Should not call services.create_service
            mock_services.create_service.assert_not_called()
            # Should use the user-provided service
            user_service.process.assert_called_once_with("test text")

    def test_error_handling_service_injection(self):
        """Test error handling when service injection fails."""
        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.side_effect = Exception(
                "Service creation failed"
            )

            @service("invalid_service")
            def test_function(text: str, invalid_service=None):
                return invalid_service.process(text)

            with pytest.raises(Exception, match="Service creation failed"):
                test_function("test text")

    def test_error_handling_config_injection(self):
        """Test error handling when config injection fails."""
        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = Exception("Config lookup failed")

            # this invalid key will show up in the Knwl logging
            @inject_config("unit.tests.invalid.config.key")
            def test_function(key=None):
                return key

            with pytest.raises(Exception, match="Config lookup failed"):
                test_function()

    def test_complex_service_specs_validation(self):
        """Test validation of complex service specifications in inject_services."""

        # Test invalid service spec
        with pytest.raises(ValueError, match="Invalid service specification"):

            @inject_services(invalid_param=123)  # Invalid spec type
            def test_function(invalid_param=None):
                pass

    def test_function_signature_binding(self):
        """Test that function signature binding works correctly with various parameter types."""
        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            @service("llm")
            def test_function(
                required_param: str, optional_param: str = "default", llm=None, **kwargs
            ):
                return {
                    "required": required_param,
                    "optional": optional_param,
                    "llm_available": llm is not None,
                    "extra_kwargs": kwargs,
                }

            result = test_function("required_value", extra_arg="extra")

            assert result["required"] == "required_value"
            assert result["optional"] == "default"
            assert result["llm_available"] is True
            assert result["extra_kwargs"] == {"extra_arg": "extra"}

    def test_inject_config_with_override(self):
        """Test inject_config decorator with override parameter."""

        # Test override functionality
        @inject_config(
            "api.host", "api.port", override={"api": {"host": "override.example.com"}}
        )
        def test_function_with_override(host=None, port=None):
            return {"host": host, "port": port}

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "port"): 8080,
                ("api", "host"): "original.example.com",
            }[keys]

            result = test_function_with_override()

            # Should use override for host and original config for port
            assert result["host"] == "override.example.com"
            assert result["port"] == 8080
            # get_config should only be called once for port, not for host due to override
            mock_get_config.assert_called_once_with("api", "port")

    def test_config_injection_registration_with_override(self):
        """Test that config injection with override is properly registered."""
        override_dict = {"api": {"host": "test.override.com", "port": 9999}}
        container.register_config_injection(
            "test_func", ["api.host", "api.port"], override=override_dict
        )

        assert "test_func" in container._config_registry
        config_info = container._config_registry["test_func"]
        assert config_info["config_keys"] == ["api.host", "api.port"]
        assert config_info["override"] == override_dict

    def test_nested_override_functionality(self):
        """Test that nested override dictionaries work correctly."""

        @inject_config(
            "llm.model",
            "llm.temperature",
            "api.port",
            override={
                "llm": {"model": "gpt-4", "temperature": 0.8},
                "api": {"port": 3000},
            },
        )
        def test_nested_overrides(model=None, temperature=None, port=None):
            return {"model": model, "temperature": temperature, "port": port}

        with patch("knwl.di.get_config") as mock_get_config:
            # Mock should not be called for any key since all are overridden
            result = test_nested_overrides()

            # All values should come from overrides
            assert result["model"] == "gpt-4"
            assert result["temperature"] == 0.8
            assert result["port"] == 3000
            # get_config should not be called at all since all values are overridden
            mock_get_config.assert_not_called()

    def test_partial_nested_override(self):
        """Test nested overrides with some values from config and some from override."""

        @inject_config(
            "llm.model",
            "llm.temperature",
            "api.host",
            override={
                "llm": {"model": "override-model"}
            },  # Only override model, not temperature
        )
        def test_partial_override(model=None, temperature=None, host=None):
            return {"model": model, "temperature": temperature, "host": host}

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("llm", "temperature"): 0.5,
                ("api", "host"): "config.example.com",
            }[keys]

            result = test_partial_override()

            # model should come from override, others from config
            assert result["model"] == "override-model"
            assert result["temperature"] == 0.5
            assert result["host"] == "config.example.com"
            # get_config should be called twice (for temperature and host)
            assert mock_get_config.call_count == 2

    def test_deep_nested_override(self):
        """Test deeply nested override structures."""

        @inject_config(
            "deep.nested.key1",
            "deep.nested.key2",
            override={"deep": {"nested": {"key1": "deep_value"}}},
        )
        def test_deep_override(key1=None, key2=None):
            return {"key1": key1, "key2": key2}

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("deep", "nested", "key2"): "config_value"
            }[keys]

            result = test_deep_override()

            assert result["key1"] == "deep_value"
            assert result["key2"] == "config_value"
            mock_get_config.assert_called_once_with("deep", "nested", "key2")

    def test_defaults_decorator_basic(self):
        """Test basic defaults injection from service configuration."""

        @defaults("something")
        class TestClass:
            def __init__(self, llm=None):
                self.llm = llm

        with (
            patch("knwl.di.get_config") as mock_get_config,
            patch("knwl.di.services") as mock_services,
        ):
            # Mock the config lookups
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("something", "default"): "basic",
                ("something", "basic"): {
                    "class": "test.TestClass",
                    "llm": "@/llm/openai",
                },
            }.get(args)

            # Mock the service instantiation
            mock_llm = Mock()
            mock_services.get_service.return_value = mock_llm

            instance = TestClass()

            assert instance.llm is mock_llm
            mock_services.get_service.assert_called_once_with(
                "llm", variant_name="openai", override=None
            )

    def test_defaults_decorator_with_variant(self):
        """Test defaults injection with explicit variant."""

        @defaults("llm", variant="ollama")
        class TestClass:
            def __init__(self, model=None, temperature=None):
                self.model = model
                self.temperature = temperature

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.return_value = {
                "class": "test.LLM",
                "model": "qwen2.5:14b",
                "temperature": 0.1,
                "context_window": 32768,
            }

            instance = TestClass()

            assert instance.model == "qwen2.5:14b"
            assert instance.temperature == 0.1

    def test_defaults_decorator_parameter_filtering(self):
        """Test that only matching parameters are injected."""

        @defaults("llm")
        class TestClass:
            def __init__(self, model=None, temperature=None):
                self.model = model
                self.temperature = temperature

        with patch("knwl.di.get_config") as mock_get_config:
            # Config has more parameters than constructor accepts
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "qwen2.5:14b",
                    "temperature": 0.1,
                    "context_window": 32768,  # Not in constructor
                    "caching": "json",  # Not in constructor
                },
            }.get(args)

            instance = TestClass()

            # Only model and temperature should be injected
            assert instance.model == "qwen2.5:14b"
            assert instance.temperature == 0.1

    def test_defaults_decorator_override(self):
        """Test that provided arguments override defaults."""

        @defaults("llm")
        class TestClass:
            def __init__(self, model=None, temperature=None):
                self.model = model
                self.temperature = temperature

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "qwen2.5:14b",
                    "temperature": 0.1,
                },
            }.get(args)

            # Override the model parameter
            instance = TestClass(model="custom-model")

            assert instance.model == "custom-model"  # Overridden
            assert instance.temperature == 0.1  # Injected

    def test_defaults_decorator_service_reference(self):
        """Test that service references (@/) are properly instantiated."""

        @defaults("graph_extraction")
        class TestClass:
            def __init__(self, llm=None, mode=None):
                self.llm = llm
                self.mode = mode

        with (
            patch("knwl.di.get_config") as mock_get_config,
            patch("knwl.di.services") as mock_services,
        ):

            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("graph_extraction", "default"): "basic",
                ("graph_extraction", "basic"): {
                    "class": "test.GraphExtraction",
                    "llm": "@/llm/ollama",
                    "mode": "full",
                },
            }.get(args)

            mock_llm = Mock()
            mock_services.get_service.return_value = mock_llm

            instance = TestClass()

            assert instance.llm is mock_llm
            assert instance.mode == "full"
            mock_services.get_service.assert_called_once_with(
                "llm", variant_name="ollama", override=None
            )

    def test_defaults_decorator_with_inject_config(self):
        """Test combining @defaults with @inject_config."""

        @defaults("graph_extraction")
        @inject_config("api.host", "api.port")
        class TestClass:
            def __init__(self, llm=None, mode=None, host=None, port=None):
                self.llm = llm
                self.mode = mode
                self.host = host
                self.port = port

        with (
            patch("knwl.di.get_config") as mock_get_config,
            patch("knwl.di.services") as mock_services,
        ):

            def config_side_effect(*args, **kwargs):
                if args == ("graph_extraction", "default"):
                    return "basic"
                elif args == ("graph_extraction", "basic"):
                    return {
                        "class": "test.GraphExtraction",
                        "llm": "@/llm/ollama",
                        "mode": "full",
                    }
                elif args == ("api", "host"):
                    return "localhost"
                elif args == ("api", "port"):
                    return 8080
                return None

            mock_get_config.side_effect = config_side_effect
            mock_llm = Mock()
            mock_services.get_service.return_value = mock_llm

            instance = TestClass()

            assert instance.llm is mock_llm
            assert instance.mode == "full"
            assert instance.host == "localhost"
            assert instance.port == 8080

    def test_defaults_decorator_no_default_variant(self):
        """Test handling when no default variant is specified."""

        @defaults("custom_service")
        class TestClass:
            def __init__(self, param=None):
                self.param = param

        with patch("knwl.di.get_config") as mock_get_config:
            # No default variant
            mock_get_config.return_value = None

            # Should not raise an error, just skip injection
            instance = TestClass()
            assert instance.param is None

    def test_inject_config_class_decorator(self):
        """Test inject_config decorator on a class."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "host"): "class.example.com",
                ("api", "port"): 9000,
            }.get(keys, None)

            @inject_config("api.host", "api.port")
            class TestService:
                def __init__(self, host=None, port=None):
                    self.host = host
                    self.port = port

            instance = TestService()
            assert instance.host == "class.example.com"
            assert instance.port == 9000

    def test_inject_config_class_with_dict_format(self):
        """Test inject_config decorator on a class with dictionary format."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("chunking", "tiktoken", "model"): "gpt-4",
                ("chunking", "tiktoken", "size"): 512,
            }.get(keys, None)

            @inject_config(
                {
                    "chunking.tiktoken.model": "model",
                    "chunking.tiktoken.size": "chunk_size",
                }
            )
            class ChunkingService:
                def __init__(self, model=None, chunk_size=None):
                    self.model = model
                    self.chunk_size = chunk_size

            instance = ChunkingService()
            assert instance.model == "gpt-4"
            assert instance.chunk_size == 512

    def test_inject_config_class_with_param_name(self):
        """Test inject_config decorator on a class with custom param_name."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "host"): "custom.host.com",
            }.get(keys, None)

            @inject_config("api.host", param_name="server_host")
            class TestService:
                def __init__(self, server_host=None):
                    self.host = server_host

            instance = TestService()
            assert instance.host == "custom.host.com"

    def test_inject_config_class_dict_with_additional_keys_error(self):
        """Test that dict format with additional keys raises error."""

        with pytest.raises(
            ValueError, match="Cannot use additional config keys with dictionary format"
        ):

            @inject_config({"api.host": "host"}, "api.port")
            class TestService:
                def __init__(self, host=None, port=None):
                    pass

    def test_inject_config_class_dict_with_param_name_error(self):
        """Test that dict format with param_name raises error."""

        with pytest.raises(
            ValueError, match="Cannot use param_name with dictionary format"
        ):

            @inject_config({"api.host": "host"}, param_name="custom")
            class TestService:
                def __init__(self, host=None):
                    pass

    def test_inject_config_function_dict_with_additional_keys_error(self):
        """Test that function decorator dict format with additional keys raises error."""

        with pytest.raises(
            ValueError, match="Cannot use additional config keys with dictionary format"
        ):

            @inject_config({"api.host": "host"}, "api.port")
            def test_function(host=None, port=None):
                pass

    def test_inject_config_function_dict_with_param_name_error(self):
        """Test that function decorator dict format with param_name raises error."""

        with pytest.raises(
            ValueError, match="Cannot use param_name with dictionary format"
        ):

            @inject_config({"api.host": "host"}, param_name="custom")
            def test_function(host=None):
                pass

    def test_inject_config_function_param_name_with_multiple_keys_error(self):
        """Test that param_name with multiple keys raises error."""

        with pytest.raises(
            ValueError, match="param_name can only be used with a single config key"
        ):

            @inject_config("api.host", "api.port", param_name="custom")
            def test_function(custom=None):
                pass

    def test_defaults_decorator_function(self):
        """Test defaults decorator on a function."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "qwen2.5:14b",
                    "temperature": 0.1,
                },
            }.get(args)

            @defaults("llm")
            def process_text(text, model=None, temperature=None):
                return {"text": text, "model": model, "temperature": temperature}

            result = process_text("hello")
            assert result["model"] == "qwen2.5:14b"
            assert result["temperature"] == 0.1

    def test_defaults_decorator_no_service_config(self):
        """Test defaults decorator when service config is not found."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("unknown_service", "default"): "variant1",
                ("unknown_service", "variant1"): None,  # No config
            }.get(args)

            @defaults("unknown_service")
            def test_function(param=None):
                return param

            result = test_function()
            assert result is None

    def test_defaults_decorator_empty_string_values(self):
        """Test that empty string values are skipped during defaults injection."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "",  # Empty string should be skipped
                    "temperature": 0.1,
                },
            }.get(args)

            @defaults("llm")
            def test_function(model=None, temperature=None):
                return {"model": model, "temperature": temperature}

            result = test_function()
            assert result["model"] is None  # Should not be injected
            assert result["temperature"] == 0.1

    def test_defaults_decorator_none_string_values(self):
        """Test that 'None' string values are skipped during defaults injection."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "none",  # 'none' string should be skipped
                    "temperature": 0.1,
                },
            }.get(args)

            @defaults("llm")
            def test_function(model=None, temperature=None):
                return {"model": model, "temperature": temperature}

            result = test_function()
            assert result["model"] is None  # Should not be injected
            assert result["temperature"] == 0.1

    def test_defaults_decorator_explicit_none_conversion(self):
        """Test that already-bound 'None' string values are converted to None."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "qwen2.5:14b",
                    "temperature": 0.1,
                },
            }.get(args)

            @defaults("llm")
            def test_function(model="None", temperature=None):
                return {"model": model, "temperature": temperature}

            # Pass "None" explicitly - this tests the bound argument conversion
            result = test_function(model="None")
            assert result["model"] is None  # Should be converted
            assert result["temperature"] == 0.1

    def test_safe_bind_partial_with_var_keyword(self):
        """Test safe_bind_partial with **kwargs parameter."""

        def func_with_kwargs(a, b=None, **kwargs):
            return {"a": a, "b": b, "kwargs": kwargs}

        bound = container.safe_bind_partial(
            func_with_kwargs, 1, b=2, extra1="x", extra2="y"
        )
        assert bound.arguments["a"] == 1
        assert bound.arguments["b"] == 2
        # Extra kwargs are collected in the 'kwargs' key
        assert "kwargs" in bound.arguments
        assert bound.arguments["kwargs"]["extra1"] == "x"
        assert bound.arguments["kwargs"]["extra2"] == "y"

    def test_safe_bind_partial_without_var_keyword(self):
        """Test safe_bind_partial filtering out invalid kwargs."""

        def func_without_kwargs(a, b=None):
            return {"a": a, "b": b}

        # Should filter out extra1 and extra2
        bound = container.safe_bind_partial(
            func_without_kwargs, 1, b=2, extra1="x", extra2="y"
        )
        assert bound.arguments["a"] == 1
        assert bound.arguments["b"] == 2
        assert "extra1" not in bound.arguments
        assert "extra2" not in bound.arguments

    def test_safe_bind_partial_with_self(self):
        """Test safe_bind_partial with class method (self parameter)."""

        class TestClass:
            def method(self, a, b=None):
                return {"a": a, "b": b}

        instance = TestClass()
        # When calling safe_bind_partial on a bound method, 'self' is already bound
        # so we just pass 'a' and other params
        bound = container.safe_bind_partial(instance.method, 1, b=2, extra="ignore")
        # The bound method already has 'self', so 'a' gets value 1
        assert "a" in bound.arguments
        assert bound.arguments["a"] == 1
        assert bound.arguments["b"] == 2
        # 'extra' should be filtered out since method doesn't accept it
        assert "extra" not in bound.arguments

    def test_get_override_value_simple(self):
        """Test _get_override_value with simple key."""
        from knwl.di import _get_override_value

        override = {"api": {"host": "test.com", "port": 8080}}
        assert _get_override_value(override, "api.host") == "test.com"
        assert _get_override_value(override, "api.port") == 8080

    def test_get_override_value_deep_nested(self):
        """Test _get_override_value with deeply nested keys."""
        from knwl.di import _get_override_value

        override = {"level1": {"level2": {"level3": {"key": "value"}}}}
        assert _get_override_value(override, "level1.level2.level3.key") == "value"

    def test_get_override_value_missing_key(self):
        """Test _get_override_value with missing key returns default."""
        from knwl.di import _get_override_value

        override = {"api": {"host": "test.com"}}
        assert _get_override_value(override, "api.missing", "default") == "default"
        assert _get_override_value(override, "missing.key", None) is None

    def test_get_override_value_empty_dict(self):
        """Test _get_override_value with empty override dict."""
        from knwl.di import _get_override_value

        assert _get_override_value({}, "any.key", "default") == "default"
        assert _get_override_value(None, "any.key", "default") == "default"

    def test_service_provider_context_manager(self):
        """Test ServiceProvider as context manager."""

        provider = ServiceProvider(api={"host": "override.com"})

        with provider as p:
            assert p is provider
            assert p.overrides == {"api": {"host": "override.com"}}

    def test_inject_config_list_format(self):
        """Test inject_config with list format."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "host"): "list.host.com",
                ("api", "port"): 7000,
            }.get(keys, None)

            @inject_config(["api.host", "api.port"])
            def test_function(host=None, port=None):
                return {"host": host, "port": port}

            result = test_function()
            assert result["host"] == "list.host.com"
            assert result["port"] == 7000

    def test_inject_config_tuple_format(self):
        """Test inject_config with tuple format."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("db", "user"): "admin",
                ("db", "password"): "secret",
            }.get(keys, None)

            @inject_config(("db.user", "db.password"))
            def test_function(user=None, password=None):
                return {"user": user, "password": password}

            result = test_function()
            assert result["user"] == "admin"
            assert result["password"] == "secret"

    def test_defaults_skip_class_parameter(self):
        """Test that 'class' parameter is skipped during defaults injection."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("service", "default"): "variant1",
                ("service", "variant1"): {
                    "class": "some.class.Name",  # Should be skipped
                    "param1": "value1",
                },
            }.get(args)

            @defaults("service")
            def test_function(param1=None):
                return {"param1": param1}

            result = test_function()
            assert result["param1"] == "value1"

    def test_wrapper_kwargs_extraction(self):
        """Test that wrapper properly extracts and merges kwargs."""

        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            @service("llm")
            def test_function(text, llm=None, **extra):
                return {"llm": llm, "extra": extra}

            result = test_function("test", custom_arg="value")

            assert result["llm"] is mock_service
            # The wrapper merges kwargs, so extra gets nested
            assert (
                "custom_arg" in result["extra"]
                or result["extra"].get("extra", {}).get("custom_arg") == "value"
            )

    def test_register_defaults_injection(self):
        """Test register_defaults_injection method."""

        container.register_defaults_injection(
            "test_func", "service_name", "variant_name", {"key": "value"}
        )

        assert "test_func" in container._defaults_registry
        defaults_info = container._defaults_registry["test_func"]
        assert defaults_info["service_name"] == "service_name"
        assert defaults_info["variant_name"] == "variant_name"
        assert defaults_info["override"] == {"key": "value"}

    def test_inject_config_with_dict_mapping(self):
        """Test inject_config function decorator with dict mapping format."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("chunking", "size"): 1024,
                ("chunking", "overlap"): 128,
            }.get(keys, None)

            @inject_config(
                {"chunking.size": "chunk_size", "chunking.overlap": "overlap_size"}
            )
            def test_function(chunk_size=None, overlap_size=None):
                return {"chunk_size": chunk_size, "overlap_size": overlap_size}

            result = test_function()
            assert result["chunk_size"] == 1024
            assert result["overlap_size"] == 128

    def test_legacy_config_injection_with_param_name(self):
        """Test legacy config injection format with custom param_name."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "endpoint"): "https://api.example.com",
            }.get(keys, None)

            @inject_config("api.endpoint", param_name="url")
            def test_function(url=None):
                return {"url": url}

            result = test_function()
            assert result["url"] == "https://api.example.com"

    def test_auto_inject_unknown_service(self):
        """Test auto_inject with unknown service parameter (should not be injected)."""

        @auto_inject
        def test_function(text: str, unknown_service=None, other_param=None):
            return {"unknown": unknown_service, "other": other_param}

        result = test_function("test")
        assert result["unknown"] is None
        assert result["other"] is None

    def test_inject_services_invalid_tuple_spec(self):
        """Test inject_services with invalid tuple specification."""

        # A tuple with wrong number of elements
        with pytest.raises(ValueError, match="Invalid service specification"):

            @inject_services(param=("service_only",))  # Tuple with only 1 element
            def test_function(param=None):
                pass

    def test_defaults_service_reference_with_variant(self):
        """Test defaults decorator with service reference that has variant."""

        with (
            patch("knwl.di.get_config") as mock_get_config,
            patch("knwl.di.services") as mock_services,
        ):

            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("service", "default"): "variant1",
                ("service", "variant1"): {
                    "class": "test.Service",
                    "llm": "@/llm",  # Service reference without variant
                },
            }.get(args)

            mock_llm = Mock()
            mock_services.get_service.return_value = mock_llm

            @defaults("service")
            def test_function(llm=None):
                return llm

            result = test_function()
            assert result is mock_llm
            # Should be called with variant_name=None when not specified
            mock_services.get_service.assert_called_once_with(
                "llm", variant_name=None, override=None
            )

    def test_inject_services_dict_spec_without_service(self):
        """Test inject_services with dict spec missing 'service' key."""

        @inject_services(param={"variant": "test", "singleton": True})
        def test_function(param=None):
            return param

        # This should handle the case where service_name is None
        # The decorator should still be applied, but injection might fail
        func_name = f"{test_function.__module__}.{test_function.__qualname__}"
        assert func_name in container._service_registry

    def test_config_injection_with_empty_override(self):
        """Test config injection when override dict is empty."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *keys: {
                ("api", "host"): "config.host.com",
            }.get(keys, None)

            @inject_config("api.host", override={})
            def test_function(host=None):
                return host

            result = test_function()
            assert result == "config.host.com"

    def test_defaults_with_none_value(self):
        """Test defaults decorator when config value is None."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("service", "default"): "variant1",
                ("service", "variant1"): {
                    "class": "test.Service",
                    "param1": None,  # Explicitly None
                    "param2": "value2",
                },
            }.get(args)

            @defaults("service")
            def test_function(param1=None, param2=None):
                return {"param1": param1, "param2": param2}

            result = test_function()
            # param1 should remain None (not injected)
            assert result["param1"] is None
            assert result["param2"] == "value2"

    def test_service_with_override(self):
        """Test service decorator with override parameter."""

        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_service

            override_config = {"llm": {"model": "custom-model"}}

            @service("llm", override=override_config)
            def test_function(llm=None):
                return llm

            result = test_function()

            mock_services.create_service.assert_called_once_with(
                "llm", variant_name=None, override=override_config
            )
            assert result is mock_service

    def test_singleton_service_with_override(self):
        """Test singleton_service decorator with override parameter."""

        mock_service = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.get_service.return_value = mock_service

            override_config = {"graph": {"backend": "networkx"}}

            @singleton_service("graph", override=override_config)
            def test_function(graph=None):
                return graph

            result = test_function()

            mock_services.get_service.assert_called_once_with(
                "graph", variant_name=None, override=override_config
            )
            assert result is mock_service

    def test_inject_services_with_override(self):
        """Test inject_services with override in dict spec."""

        mock_llm = Mock()

        with patch("knwl.di.services") as mock_services:
            mock_services.create_service.return_value = mock_llm

            @inject_services(
                llm={
                    "service": "llm",
                    "variant": "openai",
                    "singleton": False,
                    "override": {"llm": {"model": "gpt-4"}},
                }
            )
            def test_function(llm=None):
                return llm

            result = test_function()
            assert result is mock_llm

    def test_defaults_class_with_override(self):
        """Test defaults decorator on class with override."""

        with patch("knwl.di.get_config") as mock_get_config:
            mock_get_config.side_effect = lambda *args, **kwargs: {
                ("llm", "default"): "ollama",
                ("llm", "ollama"): {
                    "class": "test.LLM",
                    "model": "qwen2.5:14b",
                },
            }.get(args)

            override_config = {"llm": {"ollama": {"model": "override-model"}}}

            @defaults("llm", override=override_config)
            class TestClass:
                def __init__(self, model=None):
                    self.model = model

            instance = TestClass()
            # Should use config value since override doesn't match the structure
            assert instance.model == "qwen2.5:14b"

    def test_register_config_injection_dict_format(self):
        """Test register_config_injection with dict mapping format."""

        config_mapping = {"api.host": "server_host", "api.port": "server_port"}

        container.register_config_injection(
            "test_func",
            config_mapping,
            param_name=None,
            override={"api": {"host": "override.com"}},
        )

        assert "test_func" in container._config_registry
        config_info = container._config_registry["test_func"]
        assert config_info["config_mapping"] == config_mapping
        assert config_info["override"] == {"api": {"host": "override.com"}}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

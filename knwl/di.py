"""
Dependency Injection Framework of Knwl

This module provides decorators and utilities for dependency injection (DI) based on the config.py
configuration system. It allows methods to be decorated to automatically inject services
as dependencies.

Example usage:

    @service('llm')
    @service('vector_store', variant='chroma', param_name='storage')
    def process_documents(text: str, llm=None, storage=None):
        # llm and storage are automatically injected
        pass

    @singleton_service('graph', variant='nx')
    def get_graph_instance(graph=None):
        # graph is injected as a singleton
        pass

    @inject_config('api.host', 'api.port')
    def start_server(host=None, port=None):
        # host and port are injected from config
        pass
"""

import functools
import inspect
from typing import Any, Dict, Optional, Callable, Union

from knwl.config import get_config
from knwl.logging import log
from knwl.services import services


def _get_override_value(override_dict: Dict, config_key: str, default=None):
    """
    Get a value from a nested override dictionary using dot notation.

    Args:
        override_dict: Nested dictionary with override values
        config_key: Dot-separated key like 'api.host'
        default: Default value if key not found

    Returns:
        The value if found, otherwise default
    """
    if not override_dict:
        return default

    keys = config_key.split(".")
    current = override_dict

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


class DIContainer:
    """
    Dependency Injection Container that manages service instantiation and injection.
    """

    def __init__(self):
        self._service_registry: Dict[str, Dict] = {}
        self._config_registry: Dict[str, Dict] = {}
        self._defaults_registry: Dict[str, Dict] = {}

    def register_service_injection(self, func_name: str, service_name: str, variant_name: Optional[str] = None, param_name: Optional[str] = None, singleton: bool = False, override: Optional[Dict] = None, ):
        """Register a service injection for a function."""
        if func_name not in self._service_registry:
            self._service_registry[func_name] = {}

        injection_key = param_name or service_name
        self._service_registry[func_name][injection_key] = {"service_name": service_name, "variant_name": variant_name, "singleton": singleton, "override": override, }

    def register_config_injection(self, func_name: str, config_mapping: Union[Dict[str, str], list[str]], param_name: Optional[str] = None, override: Optional[Dict] = None, ):
        """Register config value injections for a function."""
        if isinstance(config_mapping, dict):
            # New format: {config_key: param_name}
            self._config_registry[func_name] = {"config_mapping": config_mapping, "override": override, }
        else:
            # Legacy format: list of config keys
            self._config_registry[func_name] = {"config_keys": config_mapping, "param_name": param_name, "override": override, }

    def register_defaults_injection(self, func_name: str, service_name: str, variant_name: Optional[str] = None, override: Optional[Dict] = None, ):
        """Register defaults injection from a service configuration."""
        self._defaults_registry[func_name] = {"service_name": service_name, "variant_name": variant_name, "override": override, }

    def safe_bind_partial(self, func: Callable, *args, **kwargs):
        """
        Safely bind arguments to a function, ignoring kwargs that don't match parameters.

        Args:
            func: The function to bind arguments to
            *args: Positional arguments
            **kwargs: Keyword arguments (extra ones will be filtered out)

        Returns:
            BoundArguments object with only valid parameters bound
        """
        sig = inspect.signature(func)
        valid_params = set(sig.parameters.keys())
        # Extract parameters that need to be bound (ignoring 'self' if present)
        params = list(sig.parameters.values())
        if params and params[0].name == "self":
            # Skip 'self' parameter for class methods
            params = params[1:]
            valid_params = valid_params - {"self"}

        # Filter kwargs to only include valid parameters
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

        # Check if function accepts **kwargs (VAR_KEYWORD)
        has_var_keyword = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())

        if has_var_keyword:
            # If function accepts **kwargs, include all kwargs
            bound_args = sig.bind_partial(*args, **kwargs)
        else:
            # Otherwise, only use filtered kwargs
            bound_args = sig.bind_partial(*args, **filtered_kwargs)

        bound_args.apply_defaults()
        return bound_args

    def inject_dependencies(self, func: Callable, *args, **kwargs) -> Any:
        """Inject dependencies into a function call."""
        func_name = f"{func.__module__}.{func.__qualname__}"
        sig = inspect.signature(func)

        # Use safe binding to ignore invalid kwargs
        bound_args = self.safe_bind_partial(func, *args, **kwargs)

        # Inject services
        if func_name in self._service_registry:
            for param_name, service_info in self._service_registry[func_name].items():
                if (param_name not in bound_args.arguments or bound_args.arguments[param_name] is None):
                    try:
                        if service_info["singleton"]:
                            # note that this means that accessing the singleton via injection or directly via `get_service` results in the same instance
                            service_instance = services.get_service(service_info["service_name"], variant_name=service_info["variant_name"], override=service_info["override"], )
                        else:
                            service_instance = services.create_service(service_info["service_name"], variant_name=service_info["variant_name"], override=service_info["override"], )
                        bound_args.arguments[param_name] = service_instance
                        log.debug(f"Injected service '{service_info['service_name']}' as '{param_name}' into {func.__name__}")
                    except Exception as e:
                        log(f"Failed to inject service '{service_info['service_name']}': {e}")
                        raise

        # Inject config values
        if func_name in self._config_registry:
            config_info = self._config_registry[func_name]
            override = config_info.get("override", {})

            if "config_mapping" in config_info:
                # New format: {config_key: param_name}
                config_mapping = config_info["config_mapping"]
                for config_key, param_name in config_mapping.items():
                    if (param_name not in bound_args.arguments or bound_args.arguments[param_name] is None):
                        try:
                            # Check if there's an override for this config key
                            override_value = _get_override_value(override, config_key, None)
                            if override_value is not None:
                                config_value = override_value
                                log.debug(f"Using override value for config '{config_key}' as '{param_name}' into {func.__name__}")
                            else:
                                config_value = get_config(*config_key.split("."))
                                log.debug(f"Injected config '{config_key}' as '{param_name}' into {func.__name__}")

                            bound_args.arguments[param_name] = config_value
                        except Exception as e:
                            log.error(f"Failed to inject config '{config_key}': {e}")
                            raise
            else:
                # Legacy format: list of config keys
                config_keys = config_info["config_keys"]
                custom_param_name = config_info.get("param_name")

                # Validate param_name usage
                if custom_param_name and len(config_keys) > 1:
                    raise ValueError("param_name can only be used with a single config key")

                for i, config_key in enumerate(config_keys):
                    # Use custom param_name for single config key, otherwise use last part of config key
                    if custom_param_name and len(config_keys) == 1:
                        param_name = custom_param_name
                    else:
                        param_name = config_key.split(".")[-1]  # Use last part as param name

                    if (param_name not in bound_args.arguments or bound_args.arguments[param_name] is None):
                        try:
                            # Check if there's an override for this config key
                            override_value = _get_override_value(override, config_key, None)
                            if override_value is not None:
                                config_value = override_value
                                log.debug(f"Using override value for config '{config_key}' as '{param_name}' into {func.__name__}")
                            else:
                                config_value = get_config(*config_key.split("."))
                                log.debug(f"Injected config '{config_key}' as '{param_name}' into {func.__name__}")

                            bound_args.arguments[param_name] = config_value
                        except Exception as e:
                            log.error(f"Failed to inject config '{config_key}': {e}")
                            raise

        # Inject defaults from service configuration
        if func_name in self._defaults_registry:
            defaults_info = self._defaults_registry[func_name]
            service_name = defaults_info["service_name"]
            variant_name = defaults_info.get("variant_name")
            override = defaults_info.get("override")

            # Get the default variant if not specified
            if variant_name is None:
                variant_name = get_config(service_name, "default", override=override)
                if variant_name is None:
                    log.debug(f"No default variant found for service '{service_name}', skipping defaults injection")
                    return bound_args.arguments

            # Get the service configuration
            service_config = get_config(service_name, variant_name, default=None, override=override)
            if service_config is None:
                log.debug(f"No configuration found for service '{service_name}/{variant_name}', skipping defaults injection")
                return bound_args.arguments

            # Get the function's parameter names (excluding 'self')
            valid_params = set(sig.parameters.keys())
            if "self" in valid_params:
                valid_params.remove("self")

            # Inject each config value as a parameter
            for param_name, param_value in service_config.items():
                # Skip the 'class' key as it's not a constructor parameter
                if param_name == "class":
                    continue

                # Only inject if the parameter exists in the function signature
                if param_name not in valid_params:
                    continue
                # Handle explicit "None" string to set parameter to None
                # This allows disabling a default by setting it to "None" in config
                if (bound_args.arguments[param_name] is not None and str(bound_args.arguments[param_name]).strip().lower() == "none"):
                    bound_args.arguments[param_name] = None
                    continue
                # Only inject if the parameter is not already provided
                if (param_name not in bound_args.arguments or bound_args.arguments[param_name] is None):
                    try:
                        if param_value is None:
                            continue
                        elif isinstance(param_value, str) and (param_value.strip() == "" or param_value.strip().lower() == "none"):
                            # Skip empty string values
                            continue
                        # Handle service references (e.g., "@/llm/openai")
                        elif isinstance(param_value, str) and param_value.startswith("@/"):
                            # Parse the service reference
                            ref_parts = param_value[2:].split("/")
                            if len(ref_parts) >= 1:
                                ref_service_name = ref_parts[0]
                                ref_variant_name = (ref_parts[1] if len(ref_parts) > 1 else None)
                                # fetch the singleton
                                service_instance = services.get_service(ref_service_name, variant_name=ref_variant_name, override=override, )
                                bound_args.arguments[param_name] = service_instance
                                log.debug(f"Injected service reference '{param_value}' as '{param_name}' into {func.__name__}")
                        else:
                            # Direct value injection
                            bound_args.arguments[param_name] = param_value
                            log.debug(f"Injected default '{param_name}' = '{param_value}' into {func.__name__}")
                    except Exception as e:
                        log.error(f"Failed to inject default '{param_name}' from service '{service_name}/{variant_name}': {e}")
                        raise

        return bound_args.arguments


def service(service_name: str, variant: Optional[str] = None, param_name: Optional[str] = None, override: Optional[Dict] = None, ):
    """
    Decorator to inject a service instance into a function parameter.

    Args:
        service_name: Name of the service to inject (e.g., 'llm', 'vector', 'graph')
        variant: Optional variant of the service (e.g., 'ollama', 'openai')
        param_name: Optional parameter name to inject into (defaults to service_name)
        override: Optional configuration override

    Example:
        @service('llm', variant='ollama', param_name='language_model')
        def process_text(text: str, language_model=None):
            return language_model.generate(text)
    """

    def decorator(func: Callable) -> Callable:
        func_name = f"{func.__module__}.{func.__qualname__}"
        container.register_service_injection(func_name, service_name, variant, param_name, singleton=False, override=override, )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            injected_args = container.inject_dependencies(func, *args, **kwargs)

            # Handle **kwargs properly - extract it if it exists as a separate key
            if "kwargs" in injected_args:
                extra_kwargs = injected_args.pop("kwargs")
                if isinstance(extra_kwargs, dict):
                    injected_args.update(extra_kwargs)

            return func(**injected_args)

        return wrapper

    return decorator


def singleton_service(service_name: str, variant: Optional[str] = None, param_name: Optional[str] = None, override: Optional[Dict] = None, ):
    """
    Decorator to inject a singleton service instance into a function parameter.

    Same as @service but ensures the same instance is reused across calls.

    Args:
        service_name: Name of the service to inject
        variant: Optional variant of the service
        param_name: Optional parameter name to inject into
        override: Optional configuration override

    Example:
        @singleton_service('graph', variant='nx')
        def add_node(node_data: dict, graph=None):
            graph.add_node(node_data)
    """

    def decorator(func: Callable) -> Callable:
        func_name = f"{func.__module__}.{func.__qualname__}"
        container.register_service_injection(func_name, service_name, variant, param_name, singleton=True, override=override, )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            injected_args = container.inject_dependencies(func, *args, **kwargs)

            # Handle **kwargs properly - extract it if it exists as a separate key
            if "kwargs" in injected_args:
                extra_kwargs = injected_args.pop("kwargs")
                if isinstance(extra_kwargs, dict):
                    injected_args.update(extra_kwargs)

            return func(**injected_args)

        return wrapper

    return decorator


def inject_config(config_keys_or_mapping: Union[str, Dict[str, str], list[str]], *additional_config_keys: str, param_name: Optional[str] = None, override: Optional[Dict] = None, ):
    """
    Decorator to inject configuration values into function or class constructor parameters.

    Args:
        config_keys_or_mapping: Either:
            - A single config key string (e.g., 'api.host')
            - A dictionary mapping config keys to parameter names (e.g., {'api.host': 'host', 'api.port': 'port'})
            - A list of config key strings
        *additional_config_keys: Additional configuration keys when using string format
        param_name: Optional parameter name to inject into (only works with single config key)
        override: Optional nested dictionary of config overrides matching config structure

    Examples:
        # Function decoration with string format
        @inject_config('api.host', 'api.port')
        def start_server(host=None, port=None):
            print(f"Starting server on {host}:{port}")

        # Function decoration with dictionary format
        @inject_config({
            'chunking.tiktoken.model': 'model',
            'chunking.tiktoken.size': 'chunk_size',
            'chunking.tiktoken.overlap': 'chunk_overlap'
        })
        def process_chunks(model=None, chunk_size=None, chunk_overlap=None):
            print(f"Using model {model}, size {chunk_size}, overlap {chunk_overlap}")

        # Class decoration (injects into __init__)
        @inject_config('api.host', param_name='server_host')
        class Server:
            def __init__(self, server_host=None):
                self.host = server_host

        # With override
        @inject_config('api.host', 'api.port', override={'api': {'host': 'localhost'}})
        def start_dev_server(host=None, port=None):
            print(f"Starting dev server on {host}:{port}")
    """

    def decorator(func_or_class: Callable) -> Callable:
        # Check if we're decorating a class
        if inspect.isclass(func_or_class):
            # For classes, we need to wrap the __init__ method instead of the class itself
            original_class = func_or_class
            original_init = original_class.__init__

            # Get the fully qualified name for the __init__ method
            init_func_name = (f"{original_class.__module__}.{original_class.__qualname__}.__init__")

            # Process the config keys and parameter mapping
            if isinstance(config_keys_or_mapping, dict):
                config_mapping = config_keys_or_mapping
                if additional_config_keys:
                    raise ValueError("Cannot use additional config keys with dictionary format")
                if param_name:
                    raise ValueError("Cannot use param_name with dictionary format")
            elif isinstance(config_keys_or_mapping, (list, tuple)):
                config_keys = list(config_keys_or_mapping) + list(additional_config_keys)
                config_mapping = {key: key.split(".")[-1] for key in config_keys}
            else:
                config_keys = [config_keys_or_mapping] + list(additional_config_keys)
                config_mapping = {key: key.split(".")[-1] for key in config_keys}

                if param_name:
                    if len(config_keys) > 1:
                        raise ValueError("param_name can only be used with a single config key")
                    config_mapping[config_keys[0]] = param_name

            # Register the config injection for the __init__ method
            container.register_config_injection(init_func_name, config_mapping, param_name, override)

            @functools.wraps(original_init)
            def wrapped_init(self, *args, **kwargs):
                injected_args = container.inject_dependencies(original_init, self, *args, **kwargs)

                # Handle **kwargs properly
                if "kwargs" in injected_args:
                    extra_kwargs = injected_args.pop("kwargs")
                    if isinstance(extra_kwargs, dict):
                        injected_args.update(extra_kwargs)

                return original_init(**injected_args)

            # Replace the __init__ method with our wrapped version
            original_class.__init__ = wrapped_init

            # Return the original class (not a wrapper)
            return original_class
        else:
            # For functions, use the original logic
            func_name = f"{func_or_class.__module__}.{func_or_class.__qualname__}"

            # Process the config keys and parameter mapping
            if isinstance(config_keys_or_mapping, dict):
                config_mapping = config_keys_or_mapping
                if additional_config_keys:
                    raise ValueError("Cannot use additional config keys with dictionary format")
                if param_name:
                    raise ValueError("Cannot use param_name with dictionary format")
            elif isinstance(config_keys_or_mapping, (list, tuple)):
                config_keys = list(config_keys_or_mapping) + list(additional_config_keys)
                config_mapping = {key: key.split(".")[-1] for key in config_keys}
            else:
                config_keys = [config_keys_or_mapping] + list(additional_config_keys)
                config_mapping = {key: key.split(".")[-1] for key in config_keys}

                if param_name:
                    if len(config_keys) > 1:
                        raise ValueError("param_name can only be used with a single config key")
                    config_mapping[config_keys[0]] = param_name

            container.register_config_injection(func_name, config_mapping, param_name, override)

            @functools.wraps(func_or_class)
            def wrapper(*args, **kwargs):
                injected_args = container.inject_dependencies(func_or_class, *args, **kwargs)

                # Handle **kwargs properly
                if "kwargs" in injected_args:
                    extra_kwargs = injected_args.pop("kwargs")
                    if isinstance(extra_kwargs, dict):
                        injected_args.update(extra_kwargs)

                return func_or_class(**injected_args)

            return wrapper

    return decorator


def defaults(service_name: str, variant: Optional[str] = None, override: Optional[Dict] = None, ):
    """
    Decorator to inject default values from a service configuration into class constructor parameters.

    This decorator reads the configuration for a service variant and injects those values
    as default parameters to the class constructor. If a parameter value is a service reference
    (starting with "@/"), it will be instantiated and injected.

    Args:
        service_name: Name of the service configuration to read defaults from (e.g., 'entity_extraction', 'llm')
        variant: Optional variant of the service. If None, uses the 'default' variant specified in config.
        override: Optional configuration override

    Example:
        # In config.py:
        # "entity_extraction": {
        #     "default": "basic",
        #     "basic": {
        #         "class": "knwl.extraction.basic_entity_extraction.BasicEntityExtraction",
        #         "llm": "@/llm/openai"
        #     }
        # }

        @defaults('entity_extraction')
        class BasicEntityExtraction:
            def __init__(self, llm=None):
                # llm will be automatically injected from the config
                self.llm = llm

        # You can also use it with a specific variant
        @defaults('llm', variant='ollama')
        class CustomProcessor:
            def __init__(self, model=None, temperature=None):
                # model and temperature will be injected from llm/ollama config
                pass
    """

    def decorator(func_or_class: Callable) -> Callable:
        # Check if we're decorating a class
        if inspect.isclass(func_or_class):
            # For classes, we need to wrap the __init__ method
            original_class = func_or_class
            original_init = original_class.__init__

            # Get the fully qualified name for the __init__ method
            init_func_name = (f"{original_class.__module__}.{original_class.__qualname__}.__init__")

            # Register the defaults injection for the __init__ method
            container.register_defaults_injection(init_func_name, service_name, variant, override)

            @functools.wraps(original_init)
            def wrapped_init(self, *args, **kwargs):
                injected_args = container.inject_dependencies(original_init, self, *args, **kwargs)

                # Handle **kwargs properly
                if "kwargs" in injected_args:
                    extra_kwargs = injected_args.pop("kwargs")
                    if isinstance(extra_kwargs, dict):
                        injected_args.update(extra_kwargs)

                return original_init(**injected_args)

            # Replace the __init__ method with our wrapped version
            original_class.__init__ = wrapped_init

            # Return the original class
            return original_class
        else:
            # For functions
            func_name = f"{func_or_class.__module__}.{func_or_class.__qualname__}"

            # Register the defaults injection
            container.register_defaults_injection(func_name, service_name, variant, override)

            @functools.wraps(func_or_class)
            def wrapper(*args, **kwargs):
                injected_args = container.inject_dependencies(func_or_class, *args, **kwargs)

                # Handle **kwargs properly
                if "kwargs" in injected_args:
                    extra_kwargs = injected_args.pop("kwargs")
                    if isinstance(extra_kwargs, dict):
                        injected_args.update(extra_kwargs)

                return func_or_class(**injected_args)

            return wrapper

    return decorator


def inject_services(**service_specs):
    """
    Decorator to inject multiple services with custom specifications.

    Args:
        **service_specs: Keyword arguments where key is param name and value is service spec
                        Service spec can be:
                        - str: service name (e.g., 'llm')
                        - tuple: (service_name, variant) (e.g., ('llm', 'ollama'))
                        - dict: full specification with 'service', 'variant', 'singleton', 'override'

    Example:
        @inject_services(
            llm='llm',
            storage=('vector', 'chroma'),
            graph={'service': 'graph', 'variant': 'nx', 'singleton': True}
        )
        def complex_processing(data, llm=None, storage=None, graph=None):
            # All services are automatically injected
            pass
    """

    def decorator(func: Callable) -> Callable:
        func_name = f"{func.__module__}.{func.__qualname__}"

        for param_name, spec in service_specs.items():
            if isinstance(spec, str):
                # Simple service name
                service_name = spec
                variant = None
                singleton = False
                override = None
            elif isinstance(spec, tuple) and len(spec) == 2:
                # (service_name, variant)
                service_name, variant = spec
                singleton = False
                override = None
            elif isinstance(spec, dict):
                # Full specification
                service_name = spec.get("service")
                variant = spec.get("variant")
                singleton = spec.get("singleton", False)
                override = spec.get("override")
            else:
                raise ValueError(f"Invalid service specification for {param_name}: {spec}")

            container.register_service_injection(func_name, service_name, variant, param_name, singleton, override)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            injected_args = container.inject_dependencies(func, *args, **kwargs)

            # Handle **kwargs properly - extract it if it exists as a separate key
            if "kwargs" in injected_args:
                extra_kwargs = injected_args.pop("kwargs")
                if isinstance(extra_kwargs, dict):
                    injected_args.update(extra_kwargs)

            return func(**injected_args)

        return wrapper

    return decorator


class ServiceProvider:
    """
    Context manager and utility class for managing service overrides and scoped injections.
    """

    def __init__(self, **overrides):
        """
        Initialize service provider with configuration overrides.

        Args:
            **overrides: Configuration overrides to apply during the context
        """
        self.overrides = overrides
        self._original_config = None

    def __enter__(self):
        # Store original config would go here if needed
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original config would go here if needed
        pass

    @staticmethod
    def create_service(service_name: str, variant: Optional[str] = None, override: Optional[Dict] = None, ):
        """Create a new service instance (not singleton)."""
        return services.create_service(service_name, variant_name=variant, override=override)

    @staticmethod
    def get_service(service_name: str, variant: Optional[str] = None, override: Optional[Dict] = None, ):
        """Get a singleton service instance."""
        return services.get_service(service_name, variant_name=variant, override=override)

    @staticmethod
    def clear_singletons():
        """Clear all singleton instances."""
        services.clear_singletons()


def auto_inject(func: Callable) -> Callable:
    """
    Decorator that automatically injects services based on parameter names and type hints.

    This decorator inspects the function signature and tries to inject services
    based on parameter names that match service names in the configuration.

    Example:
        @auto_inject
        def process_data(text: str, llm=None, vector=None, graph=None):
            # llm, vector, and graph are automatically injected if available
            pass
    """
    sig = inspect.signature(func)
    func_name = f"{func.__module__}.{func.__qualname__}"

    # Auto-detect services based on parameter names
    for param_name, param in sig.parameters.items():
        if param.default is None and param_name in ["llm", "vector", "graph", "json", "summarization", "chunking", "entity_extraction", "graph_extraction", ]:
            container.register_service_injection(func_name, param_name, None, param_name, singleton=True, override=None)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        injected_args = container.inject_dependencies(func, *args, **kwargs)

        # Handle **kwargs properly - extract it if it exists as a separate key
        if "kwargs" in injected_args:
            extra_kwargs = injected_args.pop("kwargs")
            if isinstance(extra_kwargs, dict):
                injected_args.update(extra_kwargs)

        return func(**injected_args)

    return wrapper


# Export the DI container for advanced usage
__all__ = ["service", "singleton_service", "inject_config", "defaults", "inject_services", "auto_inject", "ServiceProvider", "DIContainer", "container", ]

# Global DI container instance
container = DIContainer()

from typing import Any

from knwl.config import get_config
from knwl.logging import log
from knwl.utils import get_full_path, hash_args
import inspect


class Services:
    """
    A class to manage and instantiate services based on configurations.

    Note:
        - This class supports singleton instances of services, ensuring that only one
          instance of a service variant is created and reused. The singleton instances are stored
          in the `self.singletons` dictionary.
        - Services can be specified using a shorthand notation "service/variant".
    """

    def __init__(self):
        self.singletons = {}

    @staticmethod
    def parse_name(name: str) -> tuple[str, str | None]:
        """
        Parse a service name that may contain a variant specification.

        Args:
            name (str): The service name string, potentially in the format "service/variant", e.g., "json/default".
        Returns:
            tuple[str, str | None]: A tuple containing the service name and variant name.
                If no variant is specified (no "/" in the name), returns (service_name, None).
                If a variant is specified, returns (service_name, variant_name).
        Example:
            >>> parse_name("vector")
            ('vector', None)
            >>> parse_name("json/custom")
            ('json', 'custom')
        Raises:
            None
        Notes:
            - This method simply splits the input string on the first "/" character. If no "/" is found, it returns the entire string as the service name and None for the variant.
        """

        if "/" in name:
            service_name, variant_name = name.split("/", 1)
            return service_name, variant_name
        return name, None

    @staticmethod
    def get_service_specs(
        service_name: str, variant_name: str | None = None, override=None
    ) -> dict:
        """
        Retrieve the configuration/specification for a named service variant.

        This function resolves a service name and variant, supports shorthand
        "<service>/<variant>" notation, falls back to a configured default variant
        when appropriate, and returns the resolved spec dictionary with two added
        keys: "service_name" and "variant_name".

        Args:
            service_name (str): Name of the service. May be of the form "service" or
                "service/variant". Must not be None.
            variant_name (str | None): Optional variant name. If omitted, empty, or
                equal to "default" (ignoring surrounding whitespace) the configured
                default variant for the service will be used. If service_name already
                contains a slash, variant_name must be None.
            override: Optional override passed to Services.get_default_variant_name and
                get_config (implementation-specific).

        Returns:
            dict: The configuration/spec for the resolved service variant. The returned
            dict is the raw spec from configuration with two keys set/overwritten:
            "service_name" and "variant_name".

        Raises:
            ValueError: If service_name is None.
            ValueError: If service_name contains a "/" while variant_name is also provided.
            ValueError: If no default variant is configured for the service when one is required.
            ValueError: If the requested service variant is not found in configuration.

        Notes:
            - The function uses Services.parse_name to split "service/variant" form,
              Services.get_default_variant_name to determine defaults, and get_config
              to fetch the variant spec from configuration.

        Example:
            >>> override_config = {
                    "food": {
                        "default": "pizza",
                        "pizza": {"size": "large", "delivery": "transport/car"},
                        "burger": {"size": "medium"},
                    },
                    "transport": {"car": {"wheels": 4}, "bike": {"wheels": 2}},
                }
            >>> specs = services.get_service_specs("food", override=override_config)
            >>> assert specs["service_name"] == "food"
            >>> assert specs["variant_name"] == "pizza"
            >>> assert specs["size"] == "large"

        """
        if not service_name:
            raise ValueError("Service name must be provided.")
        if "/" in service_name:
            if variant_name is not None:
                raise ValueError(
                    "Can't have '/' in service name and specify a variant name at the same time."
                )
            else:
                service_name, variant_name = Services.parse_name(service_name)
        if (
            variant_name is None
            or variant_name.strip() == ""
            or variant_name.strip() == "default"
        ):
            variant_name = Services.get_default_variant_name(
                service_name, override=override
            )
            if variant_name is None:
                raise ValueError(f"No default service configured for {service_name}")
        spec = get_config(service_name, variant_name, default=None, override=override)
        if spec is None:
            raise ValueError(
                f"Service variant '{variant_name}' for {service_name} not found in configuration."
            )
        spec["service_name"] = service_name
        spec["variant_name"] = variant_name
        return spec

    @staticmethod
    def get_default_variant_name(service_name: str, override=None) -> str | None:
        """
        Every service should have a "default" key in its configuration that specifies the default service variant to use, e.g.:

        `
        "llm": {
            "default": "ollama",
            "ollama": {
                "model": "gemma3:4b",
                "temperature": 0.1,
                "context_window": 32768
            }
        }
        `

        Args:
            override: Optional dictionary to override the default configuration.
            service_name (str): The name of the service to get the default for.
        Returns:
            str: The name of the default service, or None if not found.
        Raises:
            ValueError: If the service is not found in the configuration.

        """
        return get_config(service_name, "default", default=None, override=override)

    def _get_singleton_key(
        self, service_name: str, variant_name: str = None, override=None
    ) -> str:
        """
        Return a unique string key for a singleton instance of a service.
        This computes a stable key derived from the service name, the resolved variant
        name and the variant specification (as returned by get_config). If variant_name
        is None or the literal "default", the method will resolve the default variant
        via self.get_default_variant_name(...). The computed key is produced by
        hash_args(service_name, variant_name, spec).
        
        Args:
            service_name (str): The logical name of the service. Required.
            variant_name (str, optional): The variant of the service. If None or
                "default", the default variant is resolved using
                self.get_default_variant_name(...).
            override (optional): Passed through to get_default_variant_name and
                get_config to influence configuration resolution.

        Returns:
            str: A hashed string uniquely identifying the service+variant+spec tuple.

        Raises:
            ValueError: If service_name is None.
            ValueError: If a default variant cannot be resolved for the given service.
            ValueError: If the specified service variant is not found in the configuration.
        """

        if service_name is None:
            raise ValueError("Service name must be provided to get singleton key.")
        if variant_name is None or variant_name == "default":
            variant_name = self.get_default_variant_name(
                service_name, override=override
            )
            if variant_name is None:
                raise ValueError(f"No default service configured for {service_name}")
        spec = get_config(service_name, variant_name, default=None, override=override)
        if spec is None:
            raise ValueError(
                f"Service variant '{variant_name}' for {service_name} not found in configuration."
            )
        return hash_args(service_name, variant_name, spec)

    def get_singleton(
        self, service_name: str, variant_name: str = None, override=None
    ) -> object | None:
        key = self._get_singleton_key(
            service_name, variant_name=variant_name, override=override
        )
        return self.singletons.get(key, None)

    def set_singleton(
        self, instance, service_name: str, variant_name: str = None, override=None
    ) -> object:
        key = self._get_singleton_key(
            service_name, variant_name=variant_name, override=override
        )
        self.singletons[key] = instance
        return instance

    def clear_singletons(self) -> None:
        self.singletons = {}

    def get_service(
        self, service_name: Any, variant_name: str = None, override=None
    ) -> object:
        """
        Get a singleton instance of a service. If the service has already been instantiated, return the existing instance.
        Otherwise, create a new instance and store it for future use.

        If you want to always create a new instance, use `create_service` instead.
        """
        if service_name is None:
            raise ValueError("Service name must be provided.")
        if hasattr(service_name, "__dict__"):
            return service_name  # already an instance
        if isinstance(service_name, str) and service_name.startswith("@/"):
            ref_keys = [u for u in service_name[2:].split("/") if u]
            if len(ref_keys) == 1:
                # fetch the default variant if only the service name is given
                variant_name = get_config(ref_keys[0], "default", override=override)
            else:
                variant_name = ref_keys[1]
            service_name = ref_keys[0]

        specs = self.get_service_specs(service_name, variant_name, override=override)

        service_name = specs["service_name"]
        variant_name = specs["variant_name"]
        # check the singletons cache
        found = self.get_singleton(
            service_name, variant_name=variant_name, override=override
        )
        if found:
            return found
        instance = self.create_service(
            service_name, variant_name=variant_name, override=override
        )
        self.set_singleton(
            instance, service_name, variant_name=variant_name, override=override
        )
        return instance

    def create_service(
        self, service_name: str, variant_name: str = None, override=None
    ) -> object:
        """
        Create a service instance with optional variant specification.

        Args:
            service_name (str): The name of the service to create.
            variant_name (str, optional): The specific variant of the service to instantiate.
                If None, the default service will be returned. Defaults to None.
            override (optional): Override parameters for service configuration.
                Defaults to None.

        Returns:
            The created service instance, either the default service or a specific variant
            based on the variant_name parameter.
        """
        specs = self.get_service_specs(service_name, variant_name, override=override)

        service_name = specs["service_name"]
        variant_name = specs["variant_name"]
        return self.instantiate_service(
            service_name, variant_name=variant_name, override=override
        )

    def _instantiate_service_from_specs(self, specs: dict, override=None) -> object:
        """
        Instantiate a service (or value) described by a specification dictionary.

        This helper resolves the "class" entry in a service specification and returns
        an instantiated object (or the value itself) according to the following rules:

        Behavior
        - If specs["class"] is None: raises ValueError describing the service and variant.
        - If specs["class"] is a type: removes the keys "class", "service_name", and
            "variant_name" from the specs dict and constructs the class with the
            remaining spec entries as keyword arguments.
        - If specs["class"] is a callable (but not a type): calls it with the full
            specs dict as keyword arguments and returns the result.
        - If specs["class"] is neither a str nor a type nor a callable: returns it
            directly (assumed to be an already-created instance or value).
        - If specs["class"] is a str: treats it as a fully-qualified import path
            ("module.submodule.ClassName"), imports the module, retrieves the class,
            inspects its __init__ signature, and filters specs to only those parameters
            accepted by the constructor (excluding "self"). For each parameter present
            in specs the following resolution is applied:
                - If the parameter value is a string starting with "@/": resolved via
                    get_config(..., override=override). If the resolved value is a dict
                    containing a "class" key, the dict is treated as a nested service
                    specification and recursively instantiated by this function; otherwise
                    the resolved value is used directly.
                - If the parameter value is a string starting with "$/": resolved via
                    get_full_path(...) and that value is used.
                - If the parameter value is a string equal to "none" (case-insensitive,
                    whitespace-insensitive): interpreted as None.
                - Otherwise the parameter value from specs is used unchanged.
            The class is then instantiated with the filtered and resolved keyword args.

        Parameters
        - specs (dict): Service specification dictionary. Expected keys include:
                - "class": a type, callable, instance, or import path string.
                - "service_name" (optional): used in error messages.
                - "variant_name" (optional): used in error messages.
            Additional keys may represent constructor parameters for the target class.
        - override: optional context passed to get_config when resolving "@/..." refs.

        Returns
        - object: The instantiated class instance, the return value of a callable,
            or the passed-through object/value when "class" is already an instance.

        Side effects and notes
        - When specs["class"] is a type, this function mutates the passed-in specs
            by deleting "class", "service_name", and "variant_name".
        - Import errors, attribute errors, or exceptions raised by the target class
            constructor propagate to the caller.
        - Raises ValueError when the "class" key is missing/None or when a named
            class cannot be found in the imported module.

        Dependencies
        - Uses inspect.signature to determine constructor parameters.
        - Uses get_config(...) and get_full_path(...) for special reference resolution.
        """
        class_path = specs.get("class", None)
        if class_path is None:

            service_name = specs["service_name"]
            variant_name = specs["variant_name"]
            raise ValueError(
                f"Service variant '{variant_name}' for {service_name} does not specify a class to instantiate."
            )

        if isinstance(class_path, type):
            del specs["class"]
            del specs["service_name"]
            del specs["variant_name"]
            return class_path(**specs)
        if callable(class_path):
            return class_path(**specs)
        if not isinstance(class_path, str):
            # this allows to use the override with an ad-hoc class instance rather via a namespace path
            return class_path  # Already an instance of the class

        module_name, class_name = class_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        if cls is None:
            raise ValueError(
                f"Class '{class_name}' not found in module '{module_name}'."
            )
        # Get the constructor signature
        sig = inspect.signature(cls.__init__)

        # Filter specs to only include parameters that exist in the constructor (sig are the defined params and specs are the config params)
        valid_kwargs = {}
        for param_name in sig.parameters:
            if param_name != "self" and param_name in specs:
                param_value = specs[param_name]
                # reference to another service or value
                if isinstance(param_value, str) and param_value.startswith("@/"):
                    value_ref = get_config(param_value, override=override)
                    if isinstance(value_ref, dict) and "class" in value_ref:
                        # it's a service specification
                        param = self._instantiate_service_from_specs(
                            value_ref, override=override
                        )
                    else:
                        # whatever value
                        param = value_ref
                elif isinstance(param_value, str) and param_value.startswith("$/"):
                    # it's a path reference
                    param = get_full_path(param_value)
                elif (
                    isinstance(param_value, str)
                    and param_value.strip().lower() == "none"
                ):
                    param = None
                else:
                    param = param_value
                valid_kwargs[param_name] = param

        instance = cls(**valid_kwargs)

        return instance

    def instantiate_service(
        self, service_name: str, variant_name: str = None, override=None
    ) -> object:
        """
        Instantiate a service based on its configuration specifications.
        This method retrieves service specifications and creates an instance of the specified
        service class. It supports multiple instantiation methods including direct class types,
        callable objects, string-based module paths, and pre-instantiated objects.
        Args:
            service_name (str): The name of the service to instantiate.
            variant_name (str, optional): The specific variant of the service. Defaults to None.
            override (optional): Override configuration for the service. Defaults to None.
        Returns:
            object: An instance of the requested service class.
        Note:
            - If class_path is already a type, it instantiates directly with filtered specs.
            - If class_path is callable, it calls it with all specs.
            - If class_path is not a string, it returns the object as-is (pre-instantiated).
            - For string paths, it dynamically imports the module and filters constructor
              parameters to only include valid ones from the service specifications.
        """
        specs = self.get_service_specs(service_name, variant_name, override=override)
        log(f"Instantiating service '{service_name}/{variant_name}'.")
        service_name = specs["service_name"]
        variant_name = specs["variant_name"]
        if specs is None:
            raise ValueError(
                f"Service variant '{variant_name}' for {service_name} not found in configuration."
            )
        instance = self._instantiate_service_from_specs(specs, override=override)
        instance.service_config = specs
        return instance


def get_service(service_name: str, variant_name: str = None, override=None) -> object:
    """
    An alias to `Services.get_service` for easier access.
    """
    return services.get_service(
        service_name, variant_name=variant_name, override=override
    )


def create_service(
    service_name: str, variant_name: str = None, override=None
) -> object:
    """
    An alias to `services.create_service` for easier access.
    """
    return services.create_service(
        service_name, variant_name=variant_name, override=override
    )


services = Services()

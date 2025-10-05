from knwl.config import get_config
from knwl.utils import hash_args


class Services:
    """
    A class to manage and instantiate services based on configuration.
    """

    singletons = {}

    def service_exists(self, service_name: str, override=None) -> bool:
        return get_config(service_name, default=None, override=override) is not None

    def get_default_variant_name(self, service_name: str, override=None) -> str | None:
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

    def get_singleton_key(
        self, service_name: str, variant_name: str = None, override=None
    ) -> str:
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
        key = self.get_singleton_key(
            service_name, variant_name=variant_name, override=override
        )
        return self.singletons.get(key, None)

    def set_singleton(
        self, instance, service_name: str, variant_name: str = None, override=None
    ) -> object:
        key = self.get_singleton_key(
            service_name, variant_name=variant_name, override=override
        )
        self.singletons[key] = instance
        return instance

    def clear_singletons(self) -> None:
        self.singletons = {}

    def get_service(
        self, service_name: str, variant_name: str = None, override=None
    ) -> object:
        """
        Get a singleton instance of a service. If the service has already been instantiated, return the existing instance.
        Otherwise, create a new instance and store it for future use.

        If you want to always create a new instance, use `create_service` instead.
        """
        if not self.service_exists(service_name, override=override):
            raise ValueError(f"Service '{service_name}' not found in configuration.")
        if variant_name is None or variant_name == "default":
            variant_name = self.get_default_variant_name(
                service_name, override=override
            )
            if variant_name is None:
                raise ValueError(f"No default service configured for {service_name}")
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
        if not self.service_exists(service_name, override=override):
            raise ValueError(f"Service '{service_name}' not found in configuration.")
        if variant_name is None:
            variant_name = self.get_default_variant_name(
                service_name, override=override
            )
            if variant_name is None:
                raise ValueError(f"No default service configured for {service_name}")
        return self.instantiate_service(
            service_name, variant=variant_name, override=override
        )

    def instantiate_service(
        self, service_name: str, variant: str = None, override=None
    ) -> object:
        if not self.service_exists(service_name):
            raise ValueError(f"Service '{service_name}' not found in configuration.")
        if variant is None or variant == "default":
            variant_name = self.get_default_variant_name(
                service_name, override=override
            )
            if variant_name is None:
                raise ValueError(f"No default service configured for {service_name}")
        else:
            variant_name = variant
        variant_specs = get_config(
            service_name, variant_name, default=None, override=override
        )
        if variant_specs is None:
            raise ValueError(
                f"Service variant '{variant_name}' for {service_name} not found in configuration."
            )
        class_path = variant_specs.get("class", None)
        if class_path is None:
            raise ValueError(
                f"Service variant '{variant_name}' for {service_name} does not specify a class to instantiate."
            )
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
        instance = cls(**variant_specs)
        # If the instance has an 'ensure_path_exists' method, call it for any 'path' attribute
        if hasattr(instance, "ensure_path_exists"):
            for attr in dir(instance):
                if "path" in attr.lower():
                    path_value = getattr(instance, attr)
                    if isinstance(path_value, str):
                        ensured_path = instance.ensure_path_exists(path_value)
                        setattr(instance, attr, ensured_path)
        return instance


services = Services()

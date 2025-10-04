from knwl.config import get_config


class Services:
    """
    A class to manage and instantiate services based on configuration.
    """

    def service_exists(self, service_name: str, override=None) -> bool:
        return get_config(service_name, default=None, override=override) is not None

    def get_default_service_name(self, service_name: str, override=None) -> str | None:
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

    def get_default_service(self, service_name: str, override=None):
        variant_name = self.get_default_service_name(service_name, override=override)
        if variant_name is None:
            raise ValueError(f"No default service configured for {service_name}")
        return self.instantiate_service(service_name, variant=variant_name)

    def instantiate_service(
        self, service_name: str, variant: str = None, override=None
    ):
        if not self.service_exists(service_name):
            raise ValueError(f"Service '{service_name}' not found in configuration.")
        if variant is None or variant == "default":
            variant_name = self.get_default_service_name(
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

import os
from abc import ABC
from pathlib import Path

from knwl.config import get_config


class FrameworkBase(ABC):
    def __init__(self, *args, **kwargs):
        pass

    def get_user_home(self) -> str:
        home = Path.home()
        if home is None:
            raise ValueError("Home directory not found")
        return str(home)

    def ensure_path_exists(self, path: str) -> str:
        if path is None:
            raise ValueError("Path cannot be None")

        # determine whether the path is an absolute path or relative path
        if not Path(path).is_absolute():
            path = os.path.join(self.get_user_home(), path)
        # if the path is a file path and not a directory, get the parent directory
        if os.path.isfile(path):
            path = os.path.dirname(path)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def get_test_dir():
        # Get the directory of the current file (framework_base.py) to ensure consistent path resolution
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, "..", "tests", "data")

    def get_param(self, keys, args=None, kwargs=None, default=None, override=None):
        """
        Utility to get parameter from kwargs, args or config in that order.
        The `override` parameter can be used to provide an override configuration dictionary, otherwise the default config will be used.

        Args:
        keys: list of keys to drill down in config
        args: positional arguments (list)
        kwargs: keyword arguments (dict)
        default: default value if not found
        override: override config dict
        """
        if len(keys) == 0:
            return None
        key = keys[-1]
        if kwargs and key in kwargs:
            return kwargs.get(key)
        if args:
            for arg in args:
                if isinstance(arg, dict) and key in arg:
                    return arg.get(key)
        return get_config(*keys, default=default, override=override)

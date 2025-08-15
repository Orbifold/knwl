import os
from abc import ABC
from pathlib import Path


class StorageBase(ABC):
    """
    Base class for diverse storage implementations.
    This class defines the interface and common properties for storage systems.
    """

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
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, "..", "..", "tests", "data")

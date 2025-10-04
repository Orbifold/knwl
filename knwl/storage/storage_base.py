import os
from abc import ABC
from pathlib import Path

from knwl.framework_base import FrameworkBase


class StorageBase(FrameworkBase, ABC):
    """
    Base class for diverse storage implementations.
    This class defines the interface and common properties for storage systems.
    """

  

    @staticmethod
    def get_test_dir():
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, "..", "..", "tests", "data")

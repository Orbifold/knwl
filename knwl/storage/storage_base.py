import os
from abc import ABC
from pathlib import Path

from knwl.framework_base import FrameworkBase


class StorageBase(FrameworkBase, ABC):
    """
    Base class for diverse storage implementations.
    This class defines the interface and common properties for storage systems.
    """
    pass
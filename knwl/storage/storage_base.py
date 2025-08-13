class StorageBase:
    """
    Base class for diverse storage implementations.
    This class defines the interface and common properties for storage systems.
    """
    namespace: str
    """
    Namespace or collection name for the storage, used to differentiate between different storage contexts.
    """
    caching: bool
    """
    Flag indicating whether caching is enabled for the storage. If False, this usually means the implementation is in-memory or does not persist data.
    This can be useful for testing or temporary data storage.
    """

    def __init__(self, namespace: str = "default", caching: bool = False):
        self.namespace = namespace
        self.caching = caching

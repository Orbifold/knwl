class StorageNameSpace:
    namespace: str
    caching: bool

    def __init__(self, namespace: str = "default", caching: bool = False):
        self.namespace = namespace
        self.caching = caching
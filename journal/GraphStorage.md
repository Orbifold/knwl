# GraphStorage

The `GraphStorage` is a low-level interface for storing and retrieving graph nodes and edges. It is designed to be flexible and can be implemented using various storage backends, such as in-memory storage, databases, or graph databases.

You can store and get dictionaries representing nodes and edges. If you want to work with `KnwlNode` and `KnwlEdge` models, you can use the `SemanticGraph`, which builds on top of the `GraphStorage`. Note that depending on the implementation you can have additional constraints. For example, the JSON implementation allows for complex nested structures, while the NetworkX implementation is more limited.
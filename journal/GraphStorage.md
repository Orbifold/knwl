# GraphStorage

The `GraphStorage` is a low-level interface for storing and retrieving graph nodes and edges. It is designed to be flexible and can be implemented using various storage backends, such as in-memory storage, databases, or graph databases.

You can store and get dictionaries representing nodes and edges. If you want to work with `KnwlNode` and `KnwlEdge` models, you can use the `SemanticGraph`, which builds on top of the `GraphStorage`. Note that depending on the implementation you can have additional constraints. For example, the JSON implementation allows for complex nested structures, while the NetworkX implementation is more limited.

The default implementation of the `GraphStorageBase` class is `NetworkXGraphStorage` and uses the `networkx` library for graph storage and manipulation. By default is will save things to the test directory, but you can change that by passing a different path to the constructor.

```python
from knwl.storage import NetworkXGraphStorage
graph = NetworkXGraphStorage(path="stuff")
graph = NetworkXGraphStorage("memory")  # In-memory storage
```

Much work went into making the API as flexible as possible and you can add things in various ways:

```python
await graph.upsert_node("a") # Add a node with just an Id
await graph.upsert_node("b", {"name": "Node B"}) # Add a node with an Id and properties
await graph.upsert_node({"id":"a", "type":"A"}) # dict
await graph.upsert_node(KnwlNode(name="a", type="A")) # KnwlNode
```

In all cases the nodes are internally dictionaries and that's also what you get:

```python
node = await graph.get_node("a")
print(node)  # {'id': 'a', 'type': 'A'}
node = await graph.upsert_node(KnwlNode(name="b", type="B"))
print(node)  # {'name': 'b', 'type': 'B',...}
```

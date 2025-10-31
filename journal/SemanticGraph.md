# SemanticGraph

The `SemanticGraph` is a higher level abstraction built on top of the [[GraphStorage]]. It uses LLMs for consolidation of information. If you are looking for a more low level graph storage without any LLM/RAG features, you should use the [[GraphStorage]] directly.

The `SemanticGraph` is responsible for:

- keeping the embeddings up to date
- consolidating node descriptions using LLMs (see [[Summarization]])
- store the graph topology
- perform similarity searches using embeddings.

Graph RAG consists really of just two key ingredients, graph extraction and graph management. The `SemanticGraph` if the graph management component. The [[GraphExtraction]] is the complementation to this, responsible for extracting nodes and edges from text.

In theory one could have a single storage or service for graph RAG. Something like Kuzu can indeed do vector, chunks and all. In the case of Kuzu there is a limitation in that it does not support embeddings of edges. This limits the types of graph RAG queries but that would still allow for a lot of graph RAG use cases.
Same for Falkor and Neo4j, maybe in the future an all-in-one solution can be implemented in a separate package.

The naming of the CRUD methods in the `SemanticGraph` are deliberately different from the underlying [[GraphStorage]]. For example, tThe store uses `upsert_node` while the semantica graph uses `embed_node`. This is to emphasize the difference in functionality. The `SemanticGraph` does not just store the node, it also creates/updates the embedding and consolidates the description using LLMs.

## Uniqueness

Strictly speaking the `id` is the primary key for nodes and edges in the graph. However, the `id` in Knwl is not a random thing (say uuid) but rather a deterministic identifier based on the content of the node/edge. This means that if you try to add the same node/edge twice, it will not create a duplicate, but rather update the existing one. This is important for deduplication and consolidation of information.

The id field is optional for nodes/edges and if you supply it yourself this means that you take responsibility for uniqueness. If you do not supply an id, one will be generated for you based on the content of the node/edge. This is done using a hash function.

The hashing is defined within `KnwlNode.hash_node()` and `KnwlEdge.hash_edge()`. You alter the fields used therein to change the uniqueness criteria. For example, the content or description is not taken into account but you could add it if you want more strict uniqueness.

The fact that the hash happens on the level of the node/edge means that this also happens independently of the underlying graph storage. So even if you switch from say Neo4j to Kuzu, the uniqueness criteria remains the same.

The id as a primary key on the model level means that:

- you can have nodes/edges with the same name/label/content as long as the id is different
- fetching a node by name is possible but not guaranteed to be unique
- you can have multiple versions of the same node/edge as long as the id is different
- the storage layer does not need to take care of the id.

The hash method use a convenient prefix (e.g. 'node|>afas9asd987') to allow easy identification of the type of object when debugging or inspecting the graph. This prefix is not used anywhere and can be altered or dropped if needed.

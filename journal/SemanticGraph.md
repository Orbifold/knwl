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

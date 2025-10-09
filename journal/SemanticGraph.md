# SemanticGraph

The `SemanticGraph` is a higher level abstraction built on top of the [[GraphStorage]]. It uses LLMs for consolidation of information. If you are looking for a more low level graph storage without any LLM/RAG features, you should use the [[GraphStorage]] directly.

The `SemanticGraph` is responsible for:

- keeping the embeddings up to date
- consolidating node descriptions using LLMs (see [[Summarization]])
- store the graph topology
- perform similarity searches using embeddings.

Graph RAG consists really of just two key ingredients, graph extraction and graph management. The `SemanticGraph` if the graph management component. The [[GraphExtraction]] is the complementation to this, responsible for extracting nodes and edges from text.

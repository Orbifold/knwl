In order to ingest and augment things in a GRAG system you need quite a few services and data types. The `GraphRAG` simplifies the complex mixture by bundling things into the following:

- the `SemanticGraph` combines graphs and embeddings
- the `RagStore` combines chunking, embedding/storage of chunks and storing documents
- the `GraphExtraction` taking care of extracting knowledge graphs out of text.

Each of these access underneath diverse storages and services. The dependency injection takes care of supplying lightweight (local) defaults allowing you to use everything without installing services (say, Postgres or Neo4j). Of course, this means that the defaults are not meant for production and scale. 

You also have the flexibility to discard things like extracting knowledge graphs without storing the underlying chunks or documents. This is done to enable easy experimentation with prompts, LLMs and parameters (say, custom Ollama models with different `num_ctx` values).



<img src="./images/GraphIngestion.png" alt="Graph Ingestion Output" width="500">

<img src="./images/Topology.png" alt="Small part of the Wikipedia article on topology" width="500">



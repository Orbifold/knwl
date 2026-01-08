
## Graph Analytics

- [Graspologic](https://github.com/graspologic-org/graspologic): a Python package for graph statistics.


## Graph RAG

- [Cognee](https://www.cognee.ai): memory for AI agents using graph-based RAG.
- [GLiNER2](https://github.com/fastino-ai/GLiNER2): Wonderful model for extraction of entities, relationships, structure and more. GLiNER2 unifies Named Entity Recognition, Text Classification, Structured Data Extraction, and Relation Extraction into a single 205M parameter model. It provides efficient CPU-based inference without requiring complex pipelines or external API dependencies. Knwl needs a description of ndes and edges and the similarity could work without it but would suffer without. GliNER does not provide info beyond the basics, it's not a full LLM but focused on structure extraction. As such, it does not really replace the default Knwl implementation. You could first extract the items and thereafter extract the descriptions, but whether this is faster than just using the default Knwl approach is uncertain. 
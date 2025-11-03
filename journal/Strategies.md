Augmentation strategies are techniques to augment a given question with additional context based on a knowledge base. The knowledge base is created by ingesting documents or pieces of information (chunks).

Clasic RAG is fairly straightforwards because it has only one data dimension: the vector embeddings of the chunks. With graph RAG you get multiple dimensions:

- nodes and node embeddings
- edges and edge embeddings
- high-level and low-level keywords, corresponding to global topic and local keywords
- chunks and chunk embeddings

In some cases you also want to:

- consider the degree of nodes and edges (page-ranking or centrality in general)
- ontology and metadata associated with nodes and edges
- rank chunks based on the amount of nodes, edges, keywords or ontology associated with them
- access nodes via hops (1-hop neighbors, 2-hop neighbors, etc.)

and more. The different strategies encapsulate these different dimensions and considerations to provide a rich augmentation of the original question. The question "what is the best strategy to use?" is like everything in AI: it depends. Different strategies may work better for different types of questions, knowledge bases, and desired outcomes. Experimentation and evaluation are key to finding the most effective approach for a given scenario.

Knwl comes with some predefined strategies but the `StrategyBase` class can be extended to create custom strategies that fit specific needs. The important (and complex) bits are implemented in the base class, so creating a new strategy is often a matter of configuring parameters and combining existing methods in new ways. For example, if you want to find the nearest nodes for some input and rank them by degree, you can use the `nearest_nodes` method. To collect the edges from these initial nodes, you can use the `edges_from_nodes` method. Finally, to get the chunks associated with these edges, you can use the `chunks_from_edges` method. By combining these methods in a new strategy class, you can create a tailored augmentation approach that suits your specific requirements.


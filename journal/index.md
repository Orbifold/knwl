# Knwl

Conceptually speaking, knwl is a knowledge management extension (package, tool API) designed to help you organize and retrieve information efficiently. It leverages advanced AI techniques to provide insights based on your unique knowledge base and input.

Technically, knwl is a graph RAG Python package that provides a set of tools and abstractions to manage knowledge graphs, perform semantic searches, and integrate with large language models (LLMs) for enhanced information retrieval and summarization.

Kwnl is short for 'knowledge' but could just as well stand for '_know well_'(as in knowing your knowledge well), '_knowledge network workflow library_', '_knwledge notes with linking_', '_keep notes, wiki and links_', '_knwoledge network and wisdom library_' or '_keep notes, write and learn_'.

The package is the culmination of years of experience working with knowledge graphs, LLMs, and information retrieval systems. It is designed to be modular, extensible, and easy to use, making it suitable for a wide range of applications, from personal knowledge management to enterprise-level information systems:

- works out of the box with minimal setup (no external services needed)
- pluggable components (storage, LLMs, embedding models, etc)
- can be used as a web service (REST API) or as a Python library
- can be used via CLI commands
- readily integrates with n8n, LangChain, LlamaIndex and others
- supports multiple storage backends (SQLite, Postgres, Neo4j, etc)
- supports multiple embedding models (OpenAI, HuggingFace, etc)
- supports multiple LLMs (OpenAI, HuggingFace, etc)
- can be configured with JSON or tuned via instance parameters
- advanced graph RAG: embedding of nodes and edges, multiple query strategies
- cusomizable ontology
- automatic graph extraction from text

You can use knwl in a variety of ways:

- extract a graph from a single chunk of text
- build a knowledge graph from a collection of documents
- use the JSON based graph store standalone or with a database backend
- turn any Neo4j or Memgraph database into a knowledge graph

At the same time, knwl is not:

- converting pdf, docx, html or other document formats to markdown (use other tools for that)
- a note taking app, for now there is no UI
- a replacement for LangChain, LlamaIndex or other RAG frameworks (it can be used alongside them though)
- a distributed ingestion towards graph RAG (see e.g. [TurstGraph](https://trustgraph.ai/))

## Position in the Graph Landscape

- AI platforms: there are plenty of agentic/AI platforms aiming for big money and market share. They essentially sell a platform. Orbifold Consulting helps customers solve business challenges and **Kwnl is a tool** to help with that. Knwl is not a platform, it is a library/package/tool that can be used to build platforms or solutions.
- databases: there are many graph databases and vendors which try to sell licenses but do not really listen to what you need or what your business challenges are. **Knwl is database agnostic and can work with multiple backends**, it does not pretend to solver all your problems by itself but our consulting services can help you build the right solution. We are vendor-agnostic and focus on solving your problems, not selling you a specific database.
- flows: you have self-service frameworks like n8n, node-red, Microsoft Power Apps and many more. They hide efficiently the details and complexity but this also means limited flexibility and customization. **Knwl is a developer tool that gives you full control** and flexibility to build your own solutions, it does not hide the complexity but helps you manage it.
- packages: there are many RAG frameworks and packages like LangChain, LlamaIndex, Haystack and others. They provide building blocks to build RAG solutions but often focus on text documents and do not leverage the full power of graph databases. **Knwl focuses on graph RAG** and provides advanced features for managing knowledge graphs, performing semantic searches, and integrating with LLMs. Orbifold Consulting can help you integrate knwl with these frameworks to build powerful RAG solutions.

## Do you need graph RAG?

Graph RAG augments retrieval with a knowledge graph, enabling structured reasoning and contextual linking. It’s ideal when:

- your domain involves complex relationships, for example: biomedical data (genes, proteins, diseases), legal documents (cases, statutes), scientific literature, or enterprise knowledge bases with entity hierarchies.
- you need multi-hop or compositional reasoning. Graph RAG can traverse paths like “Company → Product → Patent → Inventor” to answer layered questions that standard RAG struggles with.
- your documents are fragmented or interdependent. If relevant facts are scattered across multiple sources, Graph RAG can link them via graph edges to synthesize coherent answers.
- you want semantic control over retrieval. Graphs allow filtering by entity type, relationship, or path constraints—useful for compliance, explainability, or domain-specific QA. A complex ontology is indicative that graph RAG may be beneficial.
- you’re building agents that plan or reason over knowledge.

Standard RAG (vector-based retrieval over text chunks) may be insufficient when:

- chunk boundaries obscure semantic links, it retrieves isolated passages without understanding how entities relate across documents.
- embedding similarity fails for rare or symbolic queries. For example, “Which startups founded by MIT alumni received Series B funding in 2022?” requires structured filtering, not just semantic similarity.
- you need provenance and traceability. Graph RAG can trace answers back to specific nodes and edges, aiding auditability and trust.
- your data evolves frequently. Graphs can be incrementally updated with new entities and relations, while vector stores often require full re-embedding.
- domain knowledge is critical. Graphs can encode expert ontologies and constraints that guide retrieval beyond surface-level text similarity. A domain expert can't edit vector embeddings but knowledge graphs can be curated directly.

## What does graph RAG solve?

Standard RAG is all about vectorization of text. This is a strength and a weakness at the same time. Imagine you have a piece of text about Isaac Netwon:

> Isaac Newton was an English mathematician, physicist, astronomer, alchemist, theologian, and author who is widely recognised as one of the most influential scientists of all time and a key figure in the scientific revolution. His book Philosophiæ Naturalis Principia Mathematica (Mathematical Principles of Natural Philosophy), first published in 1687, laid the foundations for classical mechanics. Newton also made seminal contributions to optics and shares credit with Gottfried Wilhelm Leibniz for developing the infinitesimal calculus.

A standard RAG system will chunk this text into smaller pieces, create embeddings for each chunk, and store them in a vector database. When you ask a question about Isaac Newton, the system will retrieve the most relevant chunks based on embedding similarity.
If you ask a question about 'London' there will be no vector similarity with the above text since 'London' is not mentioned there. The system will simply not pick up the fragment. Adding the fact that 'Isaac Newton is burried in Westminster Abbey, London' means you have to re-vectorize things again. In addition, if you would want to link something completely unrelated like 'the Bootes Void' you would need to find some text which links the two concepts and re-vectorize again. Humans can't edit vector embeddings directly, they need to find text fragments which link concepts together. 

A graph makes information more manageable and allows to link things which are not necessarily present in texts. You can explicitly link London to Netwton, you explicitly remove links which are, according to a domain expert, not correct.
Of course, vectors are still necessary but you don't have to chunk and re-vectorize everything again. You can simply add nodes and edges to the graph. This is especially useful in domains where knowledge evolves frequently or where domain expertise is critical.


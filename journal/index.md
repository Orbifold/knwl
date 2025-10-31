# Knwl

Conceptually speaking, knwl is a knowledge management extension (package, tool API) designed to help you organize and retrieve information efficiently. It leverages advanced AI techniques to provide insights based on your unique knowledge base and input.

Technically, knwl is a graph RAG Python package that provides a set of tools and abstractions to manage knowledge graphs, perform semantic searches, and integrate with large language models (LLMs) for enhanced information retrieval and summarization.

Kwnl is short for 'knowledge' but could just as well stand for '*know well*'(as in knowing your knowledge well), '*knowledge network workflow library*', '*knwledge notes with linking*', '*keep notes, wiki and links*', '*knwoledge network and wisdom library*' or '*keep notes, write and learn*'.

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

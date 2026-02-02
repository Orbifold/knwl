# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %% Create a knowledge graph and ingest short text data
"""
==============================================================================================
This example shows that when ingesting data you can retrieve the documents and chunks created,
as well as the knowledge graph for a specific chunk or document.
That is, grounding is solidly in place.
==============================================================================================
"""
from knwl import Knwl, print_knwl

knwl = Knwl("short")
g = await knwl.ingest_short_text()
print_knwl(g)
# %% Retrieve all documents
docs = await knwl.get_all_documents(include_content=True)
print(f"Number of documents in the knowledge graph: {len(docs)}")
for doc in docs:
    print_knwl(doc)
# %% Retrieve the chunks of this document
chunks = await knwl.get_document_chunks(docs[0].id, include_content=True)
print(f"Number of chunks in the first document: {len(chunks)}")
for chunk in chunks:
    print_knwl(chunk)
# %% Get the graph of a chunk
chunk_id = chunks[0].id
graph = await knwl.get_graph_of_chunk(chunk_id)
print_knwl(graph)

# Verify that all nodes and edges in the graph reference the chunk_id
for node in graph.nodes:
    assert chunk_id in node.chunk_ids
for edge in graph.edges:
    assert chunk_id in edge.chunk_ids

# %% Get the graph of a document
# The graph of the document is in this case the same as the graph of the only chunk in the document, but in general
# it could aggregate multiple chunks.
doc_id = docs[0].id
graph = await knwl.get_graph_of_document(doc_id)
print_knwl(graph)

# Knwl

A clean Graph RAG implementation.

# Query modes

## Local
- 

- **low-level keywords** are matched against nodes, called the primary nodes
- **relationship neighborhood**  around these primary nodes is considered

The context consists of:

- **primary node** records/table consisting of name, type, and description
- **relationship** records/table consisting of source, target, type, and description
- **chunks** taken from the primary nodes

## Global

- **high-level keywords** are matched against edges

The context consists of:

- **node endpoints** of the edges
- **edge** records/table consisting of source, target, type, and description
- **chunks** taken from the edges

## Naive

The simply gives the question to the chunks and is added as context.

## Hybrid

The hybrid mode is a combination of the local and global modes.
It takes the local and global contexts, combines it as augmentation.

## March 2025

Tested a whole list of models (see the `comparison` directory) and found out that gemma3:4b is the fastest with good answers. At the same time, although it's good for answering it does not create the best KG. The nodes are extracted but it takes a better model to generate edges. The best result was with gemma3:27b.

The following models are best: phi4, llama3.1 and gemma3. Note that llama3.2 and llama3.3 are a total disaster.

The worst models are the thinking ones, the reasoning aspect is time consuming and does not give added value.
So, wisdom at this point is that one really needs three different models for each task: embedding, KG creation and answering.


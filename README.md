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


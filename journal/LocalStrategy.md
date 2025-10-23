The local augmentation strategy goes as follows:

- the question gets vectorized
- the nearest node embeddings delivers the 'primary' nodes
- the edges attached to all the primary nodes are collected
- the chunk id's across the primary nodes are ordered according to how many adjacent nodes also carry the same chunk id. This corresponds to making chunks more important if many relationships are found in a chunk.

The result is a collection of

- nodes with name, chunk id's and descriptions
- edges with name, chunk id's and descriptions
- chunks id's sorted (with respect to the criteria above)
- source references based on the chunks collected.

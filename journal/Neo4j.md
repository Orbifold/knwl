Unlike ChromaDB which has an out of the box embedding index, Neo4j requires you to create the vector index manually. Below is an example Cypher command to create a vector index for company embeddings:

```cypher
CREATE VECTOR INDEX `company-embeddings`
FOR (n: Company) ON (n.embedding)
OPTIONS {indexConfig: {
 `vector.dimensions`: 1536,
 `vector.similarity_function`: 'cosine'
}};
```

This only defines the index, the actual embedding data needs to be populated when creating or updating nodes.

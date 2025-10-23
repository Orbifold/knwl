The naive strategy is really just standard RAG:

- vectorize the given question
- go to the chunk store and fetch the nearest chunks.

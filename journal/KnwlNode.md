# KnwlNode

The `KnwlNode` is more strict in v2:

- the id is always generated based on the name and type (combined primary key if you wish)
- it is immuable but there is an update which clones the node with a new hash.

The [[GraphStorage]] is responsible for ensuring that nodes are unique by their id. Note that the [[GraphStorage]] actually does not store nodes but dictionaries. If you are looking for nodes with their embedding and all you need to use the [[SemanticGraph]]. The [[GraphStorage]] is more low level and is used by the [[SemanticGraph]]. It's organized in this fashion in order to allow for flexibility in storage backends. You can use the [[GraphStorage]] on its own without anything LLM/RAG.





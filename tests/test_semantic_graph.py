import pytest

from knwl.models import KnwlNode
from knwl.semantic.graph.semantic_graph import SemanticGraph

pytestmark = pytest.mark.llm

g = SemanticGraph()


@pytest.mark.asyncio
async def test_merge_descriptions():
    n1 = KnwlNode(name="n1", description="Tata is an elephant, he is a very social and likes to play with other animals.", type="Animal")
    n2 = KnwlNode(name="n2", description="When Tata is hungry, he likes to eat bananas.", type="Animal")
    await g.embed_nodes([n1, n2])
    n3 = KnwlNode(name="n3", description="Bananas are nutritious.", type="Fruit")
    sims = await g.get_similar_nodes(n3)
    assert sims is not None
    assert len(sims) > 0
    assert sims[0].id == n2.id  # likely that banana is more similar to n2 than n1
    n1_extension = KnwlNode(name="n1", description="Tata was born in the zoo of Berlin.", type="Animal")
    await g.embed_nodes([n1_extension])
    assert await g.node_count() == 2
    n1_summarized = await g.get_node_by_id(n1.id)
    # token count is small, so it's just concatenated
    assert n1_summarized.description == "Tata is an elephant, he is a very social and likes to play with other animals. Tata was born in the zoo of Berlin."
    print(n1_summarized)


@pytest.mark.asyncio
async def test_merge_node():
    n1 = KnwlNode(name="n1", description="Delicious oranges from Spain.", type="Fruit")
    n2 = KnwlNode(name="n2", description="Oranges are rich in vitamin C.", type="Fruit")
    await g.embed_node(n1)
    await g.embed_node(n2)
    assert await g.node_count() == 2


@pytest.mark.asyncio
async def test_custom_embedding():
    # you can alter the behavior of the embedding store by creating a custom class
    # that implements the upsert and query methods
    # here we create a dummy embedding store that always returns a fixed result
    # for testing purposes

    def create_class_from_dict(name, data):
        return type(name, (), data)

    async def upsert(self, data):
        return True

    async def query(self, query, top_k=5):
        return [KnwlNode(name="special", description="special", type="Special").model_dump(mode="json")]

    SpecialEmbedding = create_class_from_dict('SpecialEmbedding', {'upsert': upsert, 'query': query})
    config = {"semantic": {"local": {"graph": {"node_embeddings": SpecialEmbedding()}}}}
    c = SemanticGraph(node_embeddings="special", override=config)
    n1 = KnwlNode(name="n1", description="Delicious oranges from Spain.", type="Fruit")
    await c.embed_node(n1)
    assert await c.node_count() == 1
    sims = await c.get_similar_nodes(n1)
    assert sims is not None
    assert len(sims) > 0
    assert sims[0].name == "special"

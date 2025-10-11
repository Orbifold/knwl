import pytest

from knwl.models import KnwlEdge, KnwlGraph, KnwlNode
from knwl.semantic.graph.semantic_graph import SemanticGraph
from knwl.storage import NetworkXGraphStorage

pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_merge_node_descriptions():
    g = SemanticGraph("memory")
    n1 = KnwlNode(
        name="n1",
        description="Tata is an elephant, he is a very social and likes to play with other animals.",
        type="Animal",
    )
    n2 = KnwlNode(
        name="n2",
        description="When Tata is hungry, he likes to eat bananas.",
        type="Animal",
    )
    await g.embed_nodes([n1, n2])
    n3 = KnwlNode(name="n3", description="Bananas are nutritious.", type="Fruit")
    sims = await g.get_similar_nodes(n3, top_k=1)
    assert sims is not None
    assert len(sims) > 0

    n1_extension = KnwlNode(
        name="n1", description="Tata was born in the zoo of Berlin.", type="Animal"
    )
    await g.embed_nodes([n1_extension])
    assert await g.node_count() == 2
    n1_summarized = await g.get_node_by_id(n1.id)
    # token count is small, so it's just concatenated
    assert (
        n1_summarized.description
        == "Tata is an elephant, he is a very social and likes to play with other animals. Tata was born in the zoo of Berlin."
    )
    print(n1_summarized)


@pytest.mark.asyncio
async def test_merge_node():
    g = SemanticGraph("memory")
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
        return [
            KnwlNode(name="special", description="special", type="Special").model_dump(
                mode="json"
            )
        ]

    async def get_by_id(self, id):
        return None

    SpecialEmbedding = create_class_from_dict(
        "SpecialEmbedding", {"upsert": upsert, "query": query, "get_by_id": get_by_id}
    )
    config = {
        "semantic": {
            "local": {
                "graph": {
                    "graph-store": NetworkXGraphStorage("memory"),
                    "node_embeddings": SpecialEmbedding(),
                }
            }
        }
    }
    c = SemanticGraph(node_embeddings="special", override=config)
    n1 = KnwlNode(name="n1", description="Delicious oranges from Spain.", type="Fruit")
    await c.embed_node(n1)
    assert await c.node_count() == 1
    sims = await c.get_similar_nodes(n1)
    assert sims is not None
    assert len(sims) > 0
    assert sims[0].name == "special"


@pytest.mark.asyncio
async def test_merge_edge_descriptions():
    g = SemanticGraph("memory")
    n1 = KnwlNode(
        name="n1",
        description="Tata is an elephant, he is a very social and likes to play with other animals.",
        type="Animal",
    )
    n2 = KnwlNode(
        name="n2",
        description="When Tata is hungry, he likes to eat bananas.",
        type="Animal",
    )
    await g.embed_nodes([n1, n2])
    edge1 = KnwlEdge(
        source_id=n1.id,
        target_id=n2.id,
        description="Tata eats bananas when he is hungry.",
        type="Eats",
    )
    e1 = await g.embed_edge(edge1)
    assert await g.edge_count() == 1
    # now embed another edge with the same source and target
    edge2 = KnwlEdge(
        source_id=n1.id,
        target_id=n2.id,
        description="Tata loves bananas.",
        type="Eats",
    )
    e2 = await g.embed_edge(edge2)
    assert await g.edge_count() == 1
    e_merged = await g.get_edge_by_id(e1.id)
    # token count is small, so it's just concatenated
    assert (
        e_merged.description
        == "Tata eats bananas when he is hungry. Tata loves bananas."
    )
    print(e_merged)


@pytest.mark.asyncio
async def test_merge_graph():
    g = SemanticGraph("memory")
    fermi_dirac = KnwlNode(
        name="Fermi-Dirac",
        description="Fermi–Dirac statistics is a type of quantum statistics that applies to the physics of a system consisting of many non-interacting, identical particles that obey the Pauli exclusion principle. A result is the Fermi–Dirac distribution of particles over energy states. It is named after Enrico Fermi and Paul Dirac, each of whom derived the distribution independently in 1926.Fermi–Dirac statistics is a part of the field of statistical mechanics and uses the principles of quantum mechanics.",
        type="Statistical Mechanics",
    )
    maxwell_statistics = KnwlNode(
        name="Maxwell-Boltzmann",
        description="Maxwell-Boltzmann statistics is a type of statistical distribution that describes the behavior of particles in a gas. It is named after James Clerk Maxwell and Ludwig Boltzmann, who contributed to the development of kinetic theory.",
        type="Statistical Mechanics",
    )
    await g.embed_nodes([fermi_dirac, maxwell_statistics])
    edge1 = KnwlEdge(
        source_id=fermi_dirac.id,
        target_id=maxwell_statistics.id,
        description="Tata eats bananas when he is hungry.",
        type="Special_Case_Of",
    )
    await g.embed_edge(edge1)
    assert await g.edge_count() == 1

    fermi_dirac2 = KnwlNode(
        name="Fermi-Dirac",
        description="Before the introduction of Fermi–Dirac statistics in 1926, understanding some aspects of electron behavior was difficult due to seemingly contradictory phenomena. For example, the electronic heat capacity of a metal at room temperature seemed to come from 100 times fewer electrons than were in the electric current. It was also difficult to understand why the emission currents generated by applying high electric fields to metals at room temperature were almost independent of temperature.",
        type="Statistical Mechanics",
    )
    maxwell_statistics2 = KnwlNode(
        name="Maxwell-Boltzmann",
        description="The distribution was first derived by Maxwell in 1860 on heuristic grounds. Boltzmann later, in the 1870s, carried out significant investigations into the physical origins of this distribution. The distribution can be derived on the ground that it maximizes the entropy of the system.",
        type="Statistical Mechanics",
    )
    edge2 = KnwlEdge(
        source_id=fermi_dirac2.id,
        target_id=maxwell_statistics2.id,
        description="Maxwell-Boltzmann statistics is a special case of Fermi-Dirac statistics.",
        type="Special_Case_Of",
    )
    g2 = KnwlGraph(
        nodes=[fermi_dirac2, maxwell_statistics2], edges=[edge2], keywords=["physics"], id="graph2"
    )
     
    g_merged = await g.merge_graph(g2)
    assert await g.node_count() == 2
    assert await g.edge_count() == 1
    assert g_merged is not None
    assert g_merged.id == "graph2"
    assert g_merged.keywords == ["physics"]
    assert len(g_merged.nodes) == 2
    assert len(g_merged.edges) == 1
    # original nodes still exist
    assert g.node_exists(fermi_dirac.id)
    assert g.node_exists(maxwell_statistics.id)
    assert g.edge_exists(edge1.id)
    print(g_merged.get_node_descriptions())

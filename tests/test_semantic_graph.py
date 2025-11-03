import asyncio
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import KnwlEdge, KnwlGraph, KnwlNode
from knwl.semantic.graph.semantic_graph import SemanticGraph
from knwl.storage import NetworkXGraphStorage
from knwl.services import get_service, create_service

pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_embed_with_data():
    g = get_service("semantic_graph", "memory")
    n1 = KnwlNode(
        name="n1",
        description="Tata is an elephant, he is a very social and likes to play with other animals.",
        type="Animal",
        data={"habitat": "savannah", "age": 10},
    )
    await g.embed_nodes([n1])
    n1_retrieved = await g.get_node_by_id(n1.id)
    assert n1_retrieved is not None
    assert n1_retrieved.data is not None
    assert n1_retrieved.data["habitat"] == "savannah"
    assert n1_retrieved.data["age"] == 10
    print(n1_retrieved)


@pytest.mark.asyncio
async def test_merge_node_descriptions():
    g = SemanticGraph()
    print(g)
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
    assert await g.node_exists(n1_extension.id)

    n1_summarized = await g.get_node_by_id(n1.id)
    # token count is small, so it's just concatenated
    assert n1_summarized.description.endswith(
        "Tata is an elephant, he is a very social and likes to play with other animals. Tata was born in the zoo of Berlin."
    )

    print(n1_summarized)


@pytest.mark.asyncio
async def test_merge_node():
    # Using `create_service` instead of `get_service` to ensure a fresh instance.
    # Running all tests in the same session may share state otherwise.
    g = create_service("semantic_graph", "memory")
    n1 = KnwlNode(name="n1", description="Delicious oranges from Spain.", type="Fruit")
    n2 = KnwlNode(name="n2", description="Oranges are rich in vitamin C.", type="Fruit")
    await g.embed_node(n1)
    await g.embed_node(n2)
    assert await g.node_count() == 2


@pytest.mark.asyncio
async def test_merge_edge_descriptions():
    g = SemanticGraph()
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
    assert await g.edge_exists(e1.id)
    # now embed another edge with the same source and target
    edge2 = KnwlEdge(
        source_id=n1.id,
        target_id=n2.id,
        description="Tata loves bananas.",
        type="Eats",
    )
    e2 = await g.embed_edge(edge2)
    assert await g.edge_exists(e2.id)
    e_merged = await g.get_edge_by_id(e1.id)
    # token count is small, so it's just concatenated
    assert e_merged.description.endswith(
        "Tata eats bananas when he is hungry. Tata loves bananas."
    )
    print(e_merged)


@pytest.mark.asyncio
async def test_merge_graph():
    # emnbedding twice the same graph with overlapping nodes and edge
    # fermi --> maxwell
    g = get_service("semantic_graph", "memory")
    await g.clear()
    # await asyncio.sleep(1)  # wait for clear to propagate
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
        nodes=[fermi_dirac2, maxwell_statistics2],
        edges=[edge2],
        keywords=["physics"],
        id="graph2",
    )

    g_merged = await g.merge_graph(g2)
    # remains with the same topology
    assert await g.node_count() == 2
    assert await g.edge_count() == 1
    assert g_merged is not None
    # getting the same id, though the content has changed
    assert g_merged.id == "graph2"
    assert g_merged.keywords == ["physics"]
    assert len(g_merged.nodes) == 2
    assert len(g_merged.edges) == 1
    # original nodes still exist
    assert g.node_exists(fermi_dirac.id)
    assert g.node_exists(maxwell_statistics.id)
    assert g.edge_exists(edge1.id)
    print(g_merged.get_node_descriptions())


@pytest.mark.asyncio
async def test_node_by_name():
    g = get_service("semantic_graph", "memory")
    await g.clear()
    n1 = KnwlNode(
        name="Jung",
        description="Individuation is a process of psychological integration.",
        type="Theory",
    )
    n2 = KnwlNode(
        name="Jung",
        description="Carl Gustav Jung was a Swiss psychiatrist and psychoanalyst who founded analytical psychology.",
        type="Person",
    )
    await g.embed_node(n1)
    await g.embed_node(n2)
    found = await g.get_nodes_by_name("Jung")
    assert found is not None and len(found) == 2
    first = found[0]
    assert first.id == n1.id
    print_knwl(first)

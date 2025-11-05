import os

import pytest
from faker import Faker

from knwl.config import resolve_reference
from knwl.format import print_knwl
from knwl.knwl import Knwl
from knwl.storage.networkx_storage import NetworkXGraphStorage

pytestmark = pytest.mark.llm

fake = Faker()


@pytest.mark.asyncio
async def test_quick_start():
    # random namespace
    name_space = fake.word()
    print(f"\nUsing knowledge space: {name_space}\n")
    knwl = Knwl(name_space)

    # add a fact
    await knwl.add_fact(
        "gravity",
        "Gravity is a universal force that attracts two bodies toward each other.",
        id="fact1",
    )
    # where is the graph stored?
    actual_graphml_path = resolve_reference("@/graph/user/path")
    print(f"GraphML path: {actual_graphml_path}")
    assert os.path.exists(actual_graphml_path) is True

    # check if the fact exists
    assert (await knwl.node_exists("fact1")) is True
    graph_config = await knwl.get_config("@/graph/user")

    # can also open the file directly and check this
    storage = NetworkXGraphStorage(path=graph_config["path"])
    assert await storage.node_count() == 1
    assert await storage.node_exists("fact1") is True

    # Note: you can go and double-click the graphml file to open it in a graph viewer like yEd to visualize the graph.

    # add another fact
    await knwl.add_fact(
        "photosynthesis",
        "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.",
        id="fact2",
    )
    # two nodes should be present now
    assert await knwl.node_count() == 2

    # you can take the node returned from add_fact as an alternative
    found = await knwl.get_nodes_by_name("gravity")
    assert len(found) == 1
    gravity_node = found[0]
    found = await knwl.get_nodes_by_name("photosynthesis")
    assert len(found) == 1
    photosynthesis_node = found[0]
    await knwl.connect(
        source_name=gravity_node.name,
        target_name=photosynthesis_node.name,
        relation="Both are fundamental natural processes.",
    )

    # one edge
    assert await knwl.edge_count() == 1

    # Augmentation will fetch the gravity node, despite that it does not directly relate to photosynthesis
    # Obviously, this 1-hop result would not happen with classic RAG since the vector similarity is too low
    augmentation = await knwl.augment("What is photosynthesis?")
    print_knwl(augmentation)

    """
    ╭───────────────────────────────── 🎯 Context ─────────────────────────────────╮
    │                                                                              │
    │                                                                              │
    │ 💬 Question: Plants, Light energy, Carbon dioxide, Oxygen production,        │
    │ Chlorophyll                                                                  │
    │                                                                              │
    │                                                                              │
    │ 🔵 Nodes:                                                                    │
    │                                                                              │
    │   Name             Type   Description                                        │
    │  ──────────────────────────────────────────────────────────────────────────  │
    │   photosynthesis   Fact   Photosynthesis is the process by which green       │
    │                           plants and some other organisms use sunlight to    │
    │                           synthesize foods from carbon dioxide and water.    │
    │   gravity          Fact   Gravity is a universal force that attracts two     │
    │                           bodies toward each other.                          │
    │                                                                              │
    ╰───────────────────────── 0 chunks, 2 nodes, 1 edges ─────────────────────────╯
    
    """

    a = await knwl.ask("What is photosynthesis?")
    print_knwl(a.answer)


@pytest.mark.asyncio
async def test_knwl_ask():
    knwl = Knwl("swa", llm="ollama")
    a = await knwl.ask("What is the capital of Tanzania?")
    print_knwl(a)


@pytest.mark.asyncio
async def test_knwl_nodes():
    k = Knwl()
    name = fake.word()
    content = fake.sentence()
    id = str(fake.random_number(digits=5))
    n = await k.add_fact(name, content, id=id)
    assert n.id == id
    assert n.name == name
    assert n.description == content
    assert  await k.node_exists(id)
    found = await k.get_node_by_id(id)
    assert found is not None
    assert found.id == id

    await k.delete_node_by_id(id)
    assert not await k.node_exists(id)
    found = await k.get_node_by_id(id)
    assert found is None    

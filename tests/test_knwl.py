import os
import time

import pytest
from faker import Faker

from knwl.config import resolve_reference
from knwl.format import print_knwl
from knwl.knwl import Knwl, PromptType
from knwl.models.KnwlInput import KnwlInput
from knwl.storage.networkx_storage import NetworkXGraphStorage
from tests.library.collect import get_library_article

pytestmark = pytest.mark.llm

fake = Faker()


@pytest.mark.asyncio
async def test_quick_start():
    # random namespace
    name_space = fake.word()
    print(f"\nUsing knowledge space: {name_space}\n")
    knwl = Knwl(name_space)

    # add a fact
    await knwl.add_fact("gravity", "Gravity is a universal force that attracts two bodies toward each other.", id="fact1", )
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
    await knwl.add_fact("photosynthesis", "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.", id="fact2", )
    # two nodes should be present now
    assert await knwl.node_count() == 2

    # you can take the node returned from add_fact as an alternative
    found = await knwl.get_nodes_by_name("gravity")
    assert len(found) == 1
    gravity_node = found[0]
    found = await knwl.get_nodes_by_name("photosynthesis")
    assert len(found) == 1
    photosynthesis_node = found[0]
    await knwl.connect(source_name=gravity_node.name, target_name=photosynthesis_node.name, relation="Both are fundamental natural processes.", )

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
    assert await k.node_exists(id)
    found = await k.get_node_by_id(id)
    assert found is not None
    assert found.id == id

    await k.delete_node_by_id(id)
    assert not await k.node_exists(id)
    found = await k.get_node_by_id(id)
    assert found is None


@pytest.mark.asyncio
async def test_knwl_edges():
    kg = Knwl()
    name1 = fake.word()
    content1 = fake.sentence()
    id1 = str(fake.random_number(digits=5))
    n1 = await kg.add_fact(name1, content1, id=id1)

    name2 = fake.word()
    content2 = fake.sentence()
    id2 = str(fake.random_number(digits=5))
    n2 = await kg.add_fact(name2, content2, id=id2)

    relation = "related_to"
    e = await kg.connect(source_name=n1.name, target_name=n2.name, relation=relation)
    assert e.source_id == n1.id
    assert e.target_id == n2.id
    assert e.type == relation

    edges = await kg.get_edges_between_nodes(n1.id, n2.id)
    assert len(edges) == 1
    assert edges[0].source_id == n1.id
    assert edges[0].target_id == n2.id


@pytest.mark.asyncio
async def test_ingest():
    kg = Knwl()
    name = f"ingest_{fake.word()}"
    id = str(fake.random_number(digits=5))
    text = await get_library_article("literature", "Charles Dickens")
    input = KnwlInput(id=id, name=name, description="Test ingest", text=text)
    start_time = time.time()
    gr = await kg.ingest(input)
    end_time = time.time()
    print(f"Ingestion took {end_time - start_time:.2f} seconds")
    print_knwl(gr)


@pytest.mark.asyncio
async def test_knwl_absolute_path():
    """
    You can use and absolute path for the namespace to store the knowledge graph and vectors in a specific location.
    """
    name = fake.word()
    namespace = f"~/knwl_{name}"
    actual_path = os.path.expanduser(namespace)
    kg = Knwl(namespace=namespace, llm="ollama", model="gemma3:4b")
    input = KnwlInput(id="", name="John", description="Test node for override config", text="John Field wrote amazing piano concertos.", )
    await kg.add(input)
    assert os.path.exists(os.path.join(actual_path, "vectors")) is True
    import shutil

    shutil.rmtree(actual_path)


@pytest.mark.asyncio
async def test_knwl_prompt_access():
    knwl = Knwl()
    extraction_prompts = knwl.get_prompt(PromptType.EXTRACTION)
    assert extraction_prompts is not None
    text = fake.sentence()
    p = extraction_prompts.fast_graph_extraction(text)
    assert text in p
    print_knwl(p)
    summarization_prompts = knwl.get_prompt(PromptType.SUMMARIZATION)
    assert summarization_prompts is not None
    text = fake.sentence()
    p = summarization_prompts.summarize(text)
    assert text in p
    rag_prompts = knwl.get_prompt(PromptType.RAG)
    assert rag_prompts is not None
    text = fake.sentence()
    p = rag_prompts.self_rag(text)
    assert text in p

    constants_prompts = knwl.get_prompt(PromptType.CONSTANTS)
    assert constants_prompts is not None

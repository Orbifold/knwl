# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %%
"""
==============================================================================================
Knwl comes with a predefined set of default configurations that allow you to get started. You don't need to install anything beyond the package dependencies (ie. `uv sync`).

Of course, somewhere down the line you need a LLM service and the default is OpenAI. As such, you need to set the `OPENAI_API_KEY` environment variable to your OpenAI API key. If you have Ollama installed you can also use Ollama, see below.

The `Kwnl` class is a utility class that wraps various functionalities without having to instantiate or configure anything. It's useful for quick experiments and prototyping, but the full power of Knwl is unleashed when you start configuring your own services, spaces, and strategies.
==============================================================================================
"""
from knwl import Knwl, print_knwl

knwl = Knwl()
# %%
"""
==============================================================================================
You can ask questions directly and this uses the default LLM configured.
==============================================================================================
"""
a = await knwl.ask("DNA is the essence of life.")
print_knwl(a)  # pretty print the KnwlAnswer
print(a.answer)  # just print the answer string

"""
The above prints something like:
╭───────────────────────────────── KnwlAnswer ─────────────────────────────────╮
│                                                                              │
│   messages      [1 items]                                                    │
│   llm_model     gpt-oss:20b                                                  │
│   llm_service   ollama                                                       │
│   answer        Absolutely—DNA is the blueprint that carries the             │
│                 instructions for building and maintaining every living       │
│                 organism. Its double‑helix structure stores...               │
│   timing        7.95                                                         │
│   key           DNA is the essence of life.                                  │
│   category      none                                                         │
│   question      DNA is the essence of life.                                  │
│   from_cache    False                                                        │
│   id            answer|>0a93fcc2ba54d2c33155dcdb4893f0d6                     │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
"""

# %%
"""
==============================================================================================
How was this question answered? You can inspect the configuration used:
- @/llm shows the default LLM configuration
- the LLM service can have multiple models and variations
==============================================================================================
"""
print_knwl("@/llm")

# %%
"""
==============================================================================================
You can add single facts to the knowledge graph using the `add_fact` method.
There is no need to specify the id since this is a hash of the name the type.
The type is also optional and defaults to "Unknown".
==============================================================================================
"""
await knwl.add_fact(
    "gravity",
    "Gravity is a universal force that attracts two bodies toward each other.",
    type="Fact",
)

await knwl.add_fact(
    "photosynthesis",
    "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.",
    type="Fact",
)
await knwl.connect(
    source_name="gravity",
    target_name="photosynthesis",
    relation="Both are fundamental natural processes.",
)
# %%
"""
==============================================================================================
Of course, you typically do not create a KG manually like this.
You can add arbitrary text and ingest it using the `add` method.
==============================================================================================
"""

result = await knwl.add(
    "Quantum topology is all about knot theory and how it applies to quantum physics. Whether it's also underpinning quantum gravity remains to be seen, but it's a fascinating area of scientific exploration.",
)
# %%
print_knwl(result)
"""
╭───────────────────────────── 👁️ Knowledge Graph ──────────────────────────────╮
│ Id: bf3edc7e-8370-4525-a92f-52fde401efaf                                     │
│ Nodes: 2, Edges: 1                                                           │
│ Keywords: knot theory, scientific exploration...                             │
│                                                                              │
│                                                                              │
│ 🔵 Nodes:                                                                    │
│ Quantum Topology : concept - Quantum Topology is a field of study focusing   │
│ on the application of knot theory in quantum physics, exploring the          │
│ mathematical aspects of quantum mech...                                      │
│ Knot Theory : concept - Knot Theory is a branch of mathematics that studies  │
│ the properties of knots, which can be applied to various areas, including    │
│ quantum physics, to unde...                                                  │
│                                                                              │
│                                                                              │
│ 🔗 Edges:                                                                    │
│ node|>7a ─[mathematics]→ node|>66                                            │
╰────────────────────────────── 2 nodes, 1 edges ──────────────────────────────╯
"""


# %%
"""
==============================================================================================
Kwnl allows you to use namespaces for different knowledge spaces.
==============================================================================================
"""
knwl = Knwl("geography")
a = await knwl.ask("What is the capital of Tanzania?")
print_knwl(a)

# %%
"""
==============================================================================================
You can also specify different LLM providers and models.
==============================================================================================
"""
knwl = Knwl("swa", llm="openai", model="gpt-5-nano")
a = await knwl.ask("What is the capital of Tanzania?")
print_knwl(a)
# %%
"""
==============================================================================================
Classic RAG does not find information that is not vector-similar to the question.
However, Knwl's graph RAG can find related information via graph connections.
Below we create two nodes and connect them. Despite that "gravity" is not related to "photosynthesis" in a vector space,
the graph connection allows Knwl to find and use the gravity fact when answering a question about photosynthesis.
This is the most basic (but powerful) demonstration how graph RAG can improve over classic RAG.
==============================================================================================
"""

knwl = Knwl()

# add a fact
await knwl.add_fact("gravity", "Gravity is a universal force that attracts two bodies toward each other.", id="fact1", )

assert (await knwl.node_exists("fact1")) is True

# add another fact
await knwl.add_fact("photosynthesis", "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.", id="fact2", )

# you can take the node returned from add_fact as an alternative
found = await knwl.get_nodes_by_name("gravity")
gravity_node = found[0]
found = await knwl.get_nodes_by_name("photosynthesis")
photosynthesis_node = found[0]
# connect the two nodes
await knwl.connect(source_name=gravity_node.name, target_name=photosynthesis_node.name, relation="Both are fundamental natural processes.", )

# Augmentation will fetch the gravity node, despite that it does not directly relate to photosynthesis
# Obviously, this 1-hop result would not happen with classic RAG since the vector similarity is too low
augmentation = await knwl.augment("What is photosynthesis?")
# pretty print the augmentation result
print_knwl(augmentation)

# graph RAG question-answer
a = await knwl.ask("What is photosynthesis?")
print_knwl(a.answer)
# %%

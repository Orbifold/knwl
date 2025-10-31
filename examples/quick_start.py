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
import json
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
In order to use a knowledge graph you need to ingest data to build the graph. You can do this using the `add` method.
==============================================================================================
"""

result = await knwl.add(
    "Quantum topology is all about knot theory and how it applies to quantum physics."
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

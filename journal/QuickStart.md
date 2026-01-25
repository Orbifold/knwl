## Project Quick Start Guide

Create a new empty directory or open an existing one.
If you start from scratch:

```bash
mkdir my_knwl
cd my_knwl
uv init
uv add knwl
```

The only additional requirement is to have an LLM running somewhere. You can use OpenAI, Anthropic, Ollama or any others. Out of the box Knwl assumes Olloma running locally, you can easily change this.
To set the LLM provider and model, you can run:

```bash
from knwl.config import set_config_value
from knwl import print_knwl

set_config_value("openai", "llm.default", save=True)
set_config_value( "sk-proj-...","llm.openai.api_key", save=True)
```

This will create a file at `~/.knwl/config.json` with the new settings. You can edit this file directly too if you prefer.

From here on you can use the whole Knwl API as described in the documentation. You can also use the simplified API via the `Knwl` class:

```python
async def main():
    K = Knwl()
    a = await K.simple_ask("Who are you?")
    print_knwl(a)


if __name__ == "__main__":
    asyncio.run(main())
```

To add knowledge to the graph, you can use:

```python
async def main():
    K = Knwl()
    a = await K.add(
        "John is married to Jane. They have 2 kids and live in New York City."
    )
    print_knwl(a)


if __name__ == "__main__":
    asyncio.run(main())
```

This will return something like:

```text
╭───────────────────────────── 👁️ Knowledge Graph ─────────────────────────────╮
│ Id: 849b8e5d-b003-4098-95e5-cb4f85aacf39                                     │
│ Nodes: 3, Edges: 3                                                           │
│ Keywords: marriage, residence...                                             │
│                                                                              │
│                                                                              │
│ 🔵 Nodes:                                                                    │
│ John : person - John is a man who is married to Jane and is a father of two  │
│ children, living in New York City. John is a man who is married to Jane and  │
│ is a father of...                                                            │
│ Jane : person - Jane is a woman married to John and the mother of their two  │
│ children, residing in New York City. Jane is a woman married to John and the │
│ mother of the...                                                             │
│ New York City : geo - New York City is a major urban center in the United    │
│ States where John, Jane, and their children reside. New York City is a major │
│ urban center in the U...                                                     │
│                                                                              │
│                                                                              │
│ 🔗 Edges:                                                                    │
│ node|>93 ─[marriage]→ node|>04                                               │
│ node|>93 ─[residence]→ node|>69                                              │
│ node|>04 ─[residence]→ node|>69                                              │
╰────────────────────────────── 3 nodes, 3 edges ──────────────────────────────╯
```

Underneath the hood, Knwl uses out of the box:

- the LLM you have configured ([Ollama by default with Qwen 2.5 7B](https://ollama.com/library/qwen2.5:7b))
- ChromaDB as vector store with the built-in embedding model [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- NetworkX as an in-memory graph database.

You can of course change any of these components by changing the configuration as described in the documentation.

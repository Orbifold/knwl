# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %%
import asyncio
from knwl import GraphRAG, print_knwl

grag = GraphRAG()

# %%

extraction = await grag.extract(
        "Apple Inc. is an American multinational technology company headquartered in Cupertino, California, that designs, develops, and sells consumer electronics, computer software, and online services. It is considered one of the Big Tech technology companies, alongside Amazon, Google, Microsoft, and Facebook."
    )
print_knwl(extraction)


"""
This will output something like the following, depending on the LLM used (in this case OpenAI GPT-4o-mini):

╭───────────────────────────── 👁️ Graph Ingestion ──────────────────────────────╮
│ Document Id: doc|>b4f24303c29423e588e18074c34a3510                           │
│ Nodes: 7, Edges: 6                                                           │
│                                                                              │
│                                                                              │
│ Entities:                                                                    │
│                                                                              │
│   Type           Name                                                        │
│  ───────────────────────────                                                 │
│   organization   Apple Inc.                                                  │
│   geo            Cupertino                                                   │
│   geo            California                                                  │
│   organization   Amazon                                                      │
│   organization   Google                                                      │
│   organization   Microsoft                                                   │
│   organization   Facebook                                                    │
│                                                                              │
│                                                                              │
│                                                                              │
│ 🔗 Edges:                                                                    │
│                                                                              │
│   Type                    Source       Target                                │
│  ─────────────────────────────────────────────────                           │
│   location                Apple Inc.   Cupertino                             │
│   industry significance   Apple Inc.   California                            │
│   competition             Apple Inc.   Amazon                                │
│   competition             Apple Inc.   Google                                │
│   competition             Apple Inc.   Microsoft                             │
│   competition             Apple Inc.   Facebook                              │
│                                                                              │
╰────────────────────────────── 7 nodes, 6 edges ──────────────────────────────╯
"""

# %%

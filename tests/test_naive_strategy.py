import uuid
import pytest

from knwl import services
from knwl.format import print_knwl
from knwl.models import GragParams, KnwlDocument, KnwlGragContext, KnwlGragInput
from knwl.semantic.graph_rag.graph_rag import GraphRAG
from knwl.utils import get_full_path
import os

from tests.library.collect import get_library_article


@pytest.mark.asyncio
async def test_naive_augmentation():
    content = await get_library_article("mathematics", "Topology")
    doc = KnwlDocument(content=content, id=f"{str(uuid.uuid4())}.txt")
    grag: GraphRAG = services.get_service("graph_rag")
    await grag.ingest(doc)
    input = KnwlGragInput(
        text="Explain the concept of homeomorphism in topology.",
        name="Test Query",
        description="A test query for topology concepts.",
        params=GragParams(mode="naive"),
    )
    found = await grag.augment(input)
    print("")
    print_knwl(found, show_chunks=True, show_nodes=False, show_edges=False)

    """ 
    The above will render something like this:
    
╭───────────────────────────────── 🎯 Context ─────────────────────────────────╮
│                                                                              │
│                                                                              │
│  Question: Explain the concept of homeomorphism in topology.                 │
│                                                                              │
│                                                                              │
│ 📑 Chunks:                                                                   │
│                                                                              │
│ 📄[0] -to-one and onto, and if the inverse of the function is also           │
│ continuous, then the function is called a homeomorphism and the domain of    │
│ the function is...                                                           │
│                                                                              │
│                                                                              │
│ 📄[1] Topology (from the Greek words τόπος, 'place, location', and λόγος,    │
│ 'study') is the branch of mathematics concerned with the properties of a     │
│ geometric...                                                                 │
│                                                                              │
│                                                                              │
│ 📄[2] require distorting the space and affecting the curvature or volume.    │
│                                                                              │
│ Geometric topology                                                           │
│ Geometric topology is a branch of topology that primarily focu...            │
│                                                                              │
│                                                                              │
│ 📄[3] ic geometry. Donaldson, Jones, Witten, and Kontsevich have all won     │
│ Fields Medals for work related to topological field theory.                  │
│ The topological classif...                                                   │
│                                                                              │
│                                                                              │
│ 📄[4] en's theorem, covering spaces, and orbit spaces.)                      │
│ Wacław Sierpiński, General Topology, Dover Publications, 2000, ISBN          │
│ 0-486-41148-6                                                                │
│ Pickover, Clifford...                                                        │
│                                                                              │
│                                                                              │
╰───────────────────────── 5 chunks, 0 nodes, 0 edges ─────────────────────────╯
    """
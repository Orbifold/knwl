import pytest
from pydantic import ValidationError

from knwl.format import render_mermaid
from knwl.models import (
    KnwlEdge,
    KnwlGraph,
    KnwlModel,
    KnwlNode,
    KnwlInput,
    KnwlDocument,
)

pytestmark = pytest.mark.basic


def test_knwlnode():
    # you need at least name and type
    node1 = KnwlNode(name="Node1", type="TypeA")
    assert node1.id is not None
    assert node1.name == "Node1"
    assert node1.type == "TypeA"
    assert node1.description == ""

    with pytest.raises(ValidationError):
        KnwlNode(name="", type="TypeA")  # name cannot be empty
    with pytest.raises(ValidationError):
        KnwlNode(name="Node1", type="")  # type cannot be empty

    # deserialization
    node3 = KnwlNode(**node1.model_dump(mode="json"))
    assert node3.id == node1.id

    assert isinstance(node1, KnwlModel)


def test_knwledge():
    edge1 = KnwlEdge(source_id="a", target_id="b", type="relates_to")
    assert edge1.id is not None
    assert edge1.source_id == "a"
    assert edge1.target_id == "b"
    assert edge1.type == "relates_to"
    assert edge1.description == ""

    edge3 = KnwlEdge(source_id="a", target_id="c", type="relates_to")
    assert edge3.id != edge1.id  # different target_id
    assert edge3.id == KnwlEdge.hash_edge(edge3)
    with pytest.raises(ValidationError):
        KnwlEdge(
            source_id="", target_id="b", type="relates_to"
        )  # source_id cannot be empty
    with pytest.raises(ValidationError):
        KnwlEdge(
            source_id="a", target_id="", type="relates_to"
        )  # target_id cannot be empty
    with pytest.raises(ValidationError):
        KnwlEdge(source_id="a", target_id="b", type="")  # type cannot be empty

    # deserialization
    edge4 = KnwlEdge(**edge1.model_dump(mode="json"))
    assert edge4.id == edge1.id


def test_knwlgraph():

    g = KnwlGraph(nodes=[], edges=[])
    assert g.is_empty()
    assert g.get_node_ids() == []
    assert g.get_edge_ids() == []
    assert g.id is not None

    node1 = KnwlNode(name="a1", type="A")
    node2 = KnwlNode(name="a2", type="A")
    edge1 = KnwlEdge(source_id=node1.id, target_id=node2.id, type="connects")
    # edges must reference existing nodes
    with pytest.raises(ValueError):
        g = KnwlGraph(nodes=[], edges=[edge1])
    g = KnwlGraph(nodes=[node1, node2], edges=[edge1])
    assert g.node_exists(node1)
    assert g.node_exists(node1.id)

    print(g.model_dump(mode="json"))


def test_knwlinput():
    inp = KnwlInput(
        text="DNA sequencing is a complex process.",
        name="Test Input",
        description="A test input",
    )
    assert inp.text == "DNA sequencing is a complex process."
    assert inp.name == "Test Input"
    assert inp.description == "A test input"
    assert inp.id is not None

    with pytest.raises(ValueError):
        KnwlInput(text="", name="TestInput")  # text cannot be empty
    with pytest.raises(ValueError):
        KnwlInput(text=None, name="TestInput")  # text cannot be None

    # deserialization
    inp2 = KnwlInput(**inp.model_dump(mode="json"))
    assert inp2.id == inp.id

    input = KnwlInput(text="Some text")
    assert input.text == "Some text"
    assert input.name.startswith("Input ")
    assert input.description == ""
    assert input.id is not None


def test_merge_graphs():
    node1 = KnwlNode(name="Node1", type="TypeA")
    node2 = KnwlNode(name="Node2", type="TypeB")
    node3 = KnwlNode(name="Node3", type="TypeC")
    edge1 = KnwlEdge(source_id=node1.id, target_id=node2.id, type="relates_to")

    g1 = KnwlGraph(nodes=[node1, node3], edges=[])
    g2 = KnwlGraph(nodes=[node1, node2], edges=[edge1])

    g_merged = g1.merge(g2)
    assert len(g_merged.nodes) == 3
    assert len(g_merged.edges) == 1
    assert g_merged.node_exists(node1)
    assert g_merged.node_exists(node2)
    assert g_merged.node_exists(node3)
    assert g_merged.edge_exists(edge1)
    assert g_merged.id == g1.id  # id of merged graph is same as first graph

    render_mermaid(g_merged)

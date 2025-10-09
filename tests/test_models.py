import pytest
from pydantic import ValidationError

from knwl.models import KnwlEdge, KnwlNode


def test_knwlnode():
    # you need at least name and type
    node1 = KnwlNode(name="Node1", type="TypeA")
    assert node1.id is not None
    assert node1.name == "Node1"
    assert node1.type == "TypeA"
    assert node1.description == ""
    with pytest.raises(ValidationError):
        node1.name = "Node2"  # immutable
    # you can use the update method
    node2 = node1.update(name="Node2")
    assert node2.id is not None
    assert node2.name == "Node2"
    assert node1.id != node2.id
    assert node2.id == KnwlNode.hash_keys("Node2", "TypeA")

    with pytest.raises(ValidationError):
        KnwlNode(name="", type="TypeA")  # name cannot be empty
    with pytest.raises(ValidationError):
        KnwlNode(name="Node1", type="")  # type cannot be empty


def test_knwledge():
    edge1 = KnwlEdge(source_id="a", target_id="b", type="relates_to")
    assert edge1.id is not None
    assert edge1.source_id == "a"
    assert edge1.target_id == "b"
    assert edge1.type == "relates_to"
    assert edge1.description == ""
    with pytest.raises(ValidationError):
        edge1.source = "c"  # immutable
    # you can use the update method
    edge2 = edge1.update(description="new description")
    # primary key did not change
    assert edge2.id == edge1.id
    assert edge2.source_id == "a"
    assert edge2.target_id == "b"
    assert edge2.type == "relates_to"
    assert edge2.description == "new description"

    edge3 = KnwlEdge(source_id="a", target_id="c", type="relates_to")
    assert edge3.id != edge1.id  # different target_id
    assert edge3.id == KnwlEdge.hash_edge(edge3)
    with pytest.raises(ValidationError):
        KnwlEdge(source_id="", target_id="b", type="relates_to")  # source_id cannot be empty
    with pytest.raises(ValidationError):
        KnwlEdge(source_id="a", target_id="", type="relates_to")  # target_id cannot be empty
    with pytest.raises(ValidationError):
        KnwlEdge(source_id="a", target_id="b", type="")  # type cannot be empty

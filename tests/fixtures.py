import pytest
from knwl.models import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from faker import Faker
import random

fake = Faker()


def random_node_type():
    return random.choice(["Person", "Company", "Location"])


def random_relation_type():
    return random.choice(["knows", "works_at", "located_in", "related_to"])


@pytest.fixture
def random_node():
    selected_type = random_node_type()

    if selected_type == "Person":
        return KnwlNode(name=fake.name(), description=fake.text(), type="Person")
    elif selected_type == "Company":
        return KnwlNode(name=fake.company(), description=fake.text(), type="Company")
    else:  # Location
        return KnwlNode(name=fake.city(), description=fake.text(), type="Location")


@pytest.fixture
def random_nodes():
    nodes = []
    for _ in range(5):
        selected_type = random_node_type()
        if selected_type == "Person":
            nodes.append(
                KnwlNode(name=fake.name(), description=fake.text(), type="Person")
            )
        elif selected_type == "Company":
            nodes.append(
                KnwlNode(name=fake.company(), description=fake.text(), type="Company")
            )
        else:  # Location
            nodes.append(
                KnwlNode(name=fake.city(), description=fake.text(), type="Location")
            )
    return nodes


@pytest.fixture
def random_edge(random_nodes):
    return KnwlEdge(
        source_id=random.choice(random_nodes).id,
        target_id=random.choice(random_nodes).id,
        keywords=random_relation_type(),
        description=fake.text(),
    )


@pytest.fixture
def random_edges(random_nodes):
    edges = []
    for _ in range(5):
        edges.append(
            KnwlEdge(
                source_id=random.choice(random_nodes).id,
                target_id=random.choice(random_nodes).id,
                keywords=[random_relation_type()],
                description=fake.text(),
            )
        )
    return edges


@pytest.fixture
async def random_article():
    from tests.library.collect import get_random_library_article

    return await get_random_library_article()

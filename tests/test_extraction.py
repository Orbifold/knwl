import json
import pytest

from knwl.extraction.basic_entity_extraction import BasicEntityExtraction
from knwl.extraction.basic_graph_extraction import BasicGraphExtraction
from knwl.extraction.glean_graph_extraction import GleanGraphExtraction
from knwl.format import print_knwl
from knwl.models import KnwlEntity, KnwlExtraction

pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_extraction():
    extractor = BasicGraphExtraction()
    text = "Barack Obama was born in Hawaii. He was elected president in 2008."
    result = await extractor.extract_json(text)
    print("")
    print(json.dumps(result, indent=2))
    assert len(result["keywords"]) > 0
    assert len(result["relationships"]) > 0
    assert len(result["entities"]) > 0

    g = await extractor.extract(text)
    assert g is not None
    assert len(g.nodes) > 0
    assert g.edges is not None
    assert g.is_consistent()

    print("")
    print(g.model_dump_json(indent=2))


@pytest.mark.asyncio
async def test_extraction_specific_entities():
    text = "Barack Obama was born in Hawaii. He was elected president in 2008."

    extractor = BasicGraphExtraction()
    g = await extractor.extract(text, entities=["person"])
    assert g is not None
    assert len(g.nodes) > 0
    # assert g.get_entities("person") == ["person"]
    assert len(g.edges) == 0

    print("")
    print(g.model_dump_json(indent=2))


@pytest.mark.asyncio
async def test_extraction_multi_type():
    text = "Apple is an amazing company, they made the iPhone in California. Note that apple is also a fruit."

    extractor = BasicGraphExtraction()
    g:KnwlExtraction = await extractor.extract(text, entities=["company", "fruit"])
    assert g is not None
    print_knwl(g)

    assert len(g.get_name_by_type("fruit"))>0 and len(g.get_name_by_type("company"))>0  # company and fruit
    assert "company" in g.get_all_node_types() and "fruit" in g.get_all_node_types()
    print("")
    print(g.model_dump_json(indent=2))


@pytest.mark.asyncio
async def test_extraction_multiple():
    text = """John Field was an Irish composer and pianist.
    John Field was born in Dublin, Ireland, on July 26, 1782.
    He is best known for his development of the nocturne, a musical form that was later popularized by Frédéric Chopin.
    John Field had a tumultuous personal life, marked by struggles with alcoholism and financial difficulties.
    """

    extractor = BasicGraphExtraction()
    g = await extractor.extract(text, entities=["person"], chunk_id="abc")
    assert len(g.nodes) >= 1  # depending on the LLM
    assert g.nodes["John Field"][0].chunk_ids == ["abc"]
    print("")
    print_knwl(g)


@pytest.mark.asyncio
async def test_extraction_no_entities():
    text = "This text has no recognizable entities."

    extractor = BasicGraphExtraction()
    g = await extractor.extract(text)
    assert g is None

    


@pytest.mark.asyncio
async def test_gleaning():
    text = """Alice went to the park. There she met Bob. They decided to go for ice cream.
    Later, Alice and Bob went to see a movie together. After the movie, they had dinner at a nearby restaurant.
    """
    extractor = GleanGraphExtraction()
    g = await extractor.extract(text)
    assert g is not None
    assert len(g.nodes) > 0
    assert len(g.edges) > 0
    print("")
    print(g.model_dump_json(indent=2))


@pytest.mark.asyncio
async def test_fast_entity_extraction():
    text = "Barack Obama was born in Hawaii. He was elected president in 2008."

    extractor = BasicEntityExtraction()
    result:list[KnwlEntity] = await extractor.extract(text)
    assert result is not None
    assert len(result) > 0
    # assert len(result["relationships"]) > 0
    # assert len(result["entities"]) > 0
    result = await extractor.extract_json(text)
    assert result is not None

    print("")
    print(result)
    assert len(result) > 0

    extractor = BasicEntityExtraction()
    text = "This text has no recognizable entities and none should be found."
    result:list[KnwlEntity] = await extractor.extract(text)
    assert result is None

import pytest

from knwl.extraction.basic_extraction import BasicExtraction


@pytest.mark.asyncio
async def test_extraction():
    extractor = BasicExtraction()
    text = "Barack Obama was born in Hawaii. He was elected president in 2008."
    result = await extractor.extract_json(text)
    assert len(result["keywords"]) > 0
    assert len(result["relationships"]) > 0
    assert len(result["entities"]) > 0

    # print("")
    # print(json.dumps(result, indent=2))

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

    extractor = BasicExtraction()
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

    extractor = BasicExtraction()
    g = await extractor.extract(text, entities=["company", "fruit"])
    assert g is not None
    assert len(g.nodes["Apple"]) == 2  # company and fruit
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

    extractor = BasicExtraction()
    g = await extractor.extract(text, entities=["person"],chunk_id="abc")
    assert len(g.nodes) == 1  # only one person despite appearing multiple times
    assert g.nodes["John Field"][0].chunkIds == ["abc"]
    print("")
    print(g.model_dump_json(indent=2))

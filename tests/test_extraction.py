import pytest

from knwl.extraction.glean_extraction import GleaningExtraction


@pytest.mark.asyncio
async def test_extraction():
    extractor = GleaningExtraction()
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

    extractor = GleaningExtraction()
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

    extractor = GleaningExtraction()
    g = await extractor.extract(text, entities=["company", "fruit"])
    assert g is not None
    assert len(g.nodes["Apple"]) == 2  # company and fruit
    assert "company" in g.get_all_node_types() and "fruit" in g.get_all_node_types()
    print("")
    print(g.model_dump_json(indent=2))

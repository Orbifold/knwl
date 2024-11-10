import json
from dataclasses import asdict
from unittest import skipIf

import pytest

from knwl.entities import convert_record_to_edge, is_entity, is_relationship, extract_entities, stringify_keys, extract_entities_from_text
from knwl.utils import *
from knwl.entities import convert_record_to_node


class TestBasic:

    @pytest.mark.asyncio
    async def test_extract_relationship(self):
        record_attributes = [
            "relationship",
            'source_entity',
            'target_entity',
            'description, of the      relationship',
            'k1,  k2, k3',
            '4.0'
        ]
        chunk_key = 'chunk_1'

        expected_result = KnwlEdge(**{
            'sourceId': clean_str(record_attributes[1].upper()),
            'targetId': clean_str(record_attributes[2].upper()),
            'weight': 4.0,
            'description': clean_str(record_attributes[3]),
            'keywords': clean_str(record_attributes[4]),
            'chunkIds': chunk_key
        })

        result = await convert_record_to_edge(record_attributes, chunk_key)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_extract_relationship_with_default_weight(self):
        record_attributes = [
            "relationship",
            'source_entity',
            'target_entity',
            'description of the relationship',
            'A,B,D,    K1, K2, K3'
        ]
        chunk_key = 'chunk_2'

        expected_result = KnwlEdge(**{
            'sourceId': clean_str(record_attributes[1].upper()),
            'targetId': clean_str(record_attributes[2].upper()),
            'weight': 1.0,
            'description': clean_str(record_attributes[3]),
            'keywords': clean_str(record_attributes[4]),
            'chunkIds': chunk_key
        })

        result = await convert_record_to_edge(record_attributes, chunk_key)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_extract_entity(self):
        record_attributes = [
            "entity",
            'some     name, here',
            'entity_type',
            'description of the entity'
        ]
        chunk_key = 'chunk_1'

        expected_result = KnwlNode(**{
            'name': clean_str(record_attributes[1].upper()),
            'type': clean_str(record_attributes[2].upper()),
            'description': clean_str(record_attributes[3]),
            'chunkIds': chunk_key
        })

        result = await convert_record_to_node(record_attributes, chunk_key)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_extract_entity_with_empty_name(self):
        record_attributes = [
            "entity",
            '',
            'entity_type',
            'description of the entity'
        ]
        chunk_key = 'chunk_2'

        result = await convert_record_to_node(record_attributes, chunk_key)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_entity_with_whitespace_name(self):
        record_attributes = [
            "entity",
            '   ',
            'entity_type',
            'description of the entity'
        ]
        chunk_key = 'chunk_3'

        result = await convert_record_to_node(record_attributes, chunk_key)
        assert result is None

    def test_is_relationship(self):
        assert is_relationship(
            ["relationship", 'source', 'target', 'description', 'keywords']) == True
        assert is_relationship(
            ["relationship", 'source', 'target', 'description']) == False
        assert is_relationship(
            ["entity", 'source', 'target', 'description', 'keywords']) == False
        assert is_relationship(["relationship", 'source',
                                'target', 'description', 'keywords', 'extra']) == True
        assert is_relationship([]) == False
        assert is_relationship(None) == False

    def test_is_entity(self):
        assert is_entity(["entity", 'name', 'type', 'description']) == True
        assert is_entity(["entity", 'name', 'type']) == False
        assert is_entity(
            ["relationship", 'name', 'type', 'description']) == False
        assert is_entity(["entity", 'name', 'type',
                          'description', 'extra']) == True
        assert is_entity([]) == False
        assert is_entity(None) == False


@pytest.mark.skip("Not relevant for the current implementation")
class TestActualExtraction:

    @pytest.mark.asyncio
    async def test_extract_two_people(self):
        chunks = {
            "a": KnwlChunk(content="John knows Maria.", tokens=3)
        }

        g: KnwlExtraction = await extract_entities(chunks)

        print(">>", json.dumps(asdict(g), indent=2))

        assert len(g.nodes) == 2
        assert len(g.edges) == 1
        assert "JOHN" in g.nodes
        assert len(g.nodes["JOHN"]) >= 1
        assert g.nodes["JOHN"][0].type == "PERSON"
        assert len(g.nodes["MARIA"]) == 1
        assert g.nodes["MARIA"][0].type == "PERSON"

    @pytest.mark.asyncio
    async def test_multiple_descriptions(self):
        chunks = {
            "a": KnwlChunk(content="John is an artist.", tokens=4),
            "b": KnwlChunk(content="John works in a museum in Chelsea.", tokens=7)
        }

        g: KnwlExtraction = await extract_entities(chunks)

        print(json.dumps(asdict(g), indent=2))

        assert "JOHN" in g.nodes
        # likely three descriptions of who John is
        assert len(g.nodes["JOHN"]) > 1

    @pytest.mark.asyncio
    async def test_extract_from_text(self):
        text = "John is an artist. He works in a museum in Chelsea. He knows Maria."
        found = await extract_entities_from_text(text)
        print()
        print(json.dumps(asdict(found), indent=2))

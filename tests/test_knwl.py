import json
from dataclasses import asdict
from typing import List

import pytest
import pytest_asyncio
from faker import Faker

# Mark entire module as requiring LLM integration
# All tests in this module will be skipped in CI environments
pytestmark = pytest.mark.llm

import knwl
from knwl.knwl import Knwl
from knwl.models import KnwlLLMAnswer
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlInput import KnwlInput
from knwl.models.KnwlNode import KnwlNode
from knwl.models.KnwlResponse import KnwlResponse
from knwl.models.QueryParam import QueryParam
from knwl.prompt import GRAPH_FIELD_SEP
from knwl.tokenize import count_tokens
from knwl.utils import hash_with_prefix

faker = Faker()


def create_dummy_documents(n=10):
    sources = {}
    for i in range(n):
        source = KnwlDocument(content=faker.text(), name=faker.catch_phrase(), description=faker.sentence())
        sources[source.id] = source
    return sources


class TestRealCases:
    @pytest_asyncio.fixture
    async def knwl(cls):
        cls.knwl = Knwl()
        await cls.knwl.input('John is married to Anna.', "Married")
        await cls.knwl.input('Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.', "Family")
        await cls.knwl.input('John has been working for the past ten years on AI and robotics. He knows a lot about the subject.', "Work")
        return cls.knwl

    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_local(self, knwl):
        response = await knwl.query("Who is John?", QueryParam(mode="local"))

        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)
        print()
        print("======================== References =====================================")
        print(response.context.get_references_table())
        print("======================== Timing =====================================")
        print(f"timing: {response.total_time}s [{response.rag_time}s rag, {response.llm_time}s llm]")

    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_global(self, knwl):
        response = await knwl.query("Who is John?", QueryParam(mode="global"))
        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)
        print()
        print("======================== References =====================================")
        print(response.context.get_references_table())
        print("======================== Timing =====================================")
        # print(f"llm: {response.total_time}s")
        print(f"total: {response.total_time}s")
        print("======================== Timing =====================================")
        print(f"timing: {response.total_time}s [{response.rag_time}s rag, {response.llm_time}s llm]")

    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_naive(self, knwl):
        response = await knwl.query("Who is John?", QueryParam(mode="naive"))
        print()
        print("======================== Context ====================================")
        print(response.context.get_documents())
        print()
        print("======================== Answer =====================================")
        print(response.answer)
        print()
        print("======================== References =====================================")
        print(response.context.get_references_table())
        print("======================== Timing =====================================")
        print(f"timing: {response.total_time}s [{response.rag_time}s rag, {response.llm_time}s llm]")

    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_hybrid(self, knwl):
        response = await knwl.query("Who is John?", QueryParam(mode="hybrid"))
        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)
        print()
        print("======================== References =====================================")
        print(response.context.get_references_table())
        print("======================== Timing =====================================")
        print(f"timing: {response.total_time}s [{response.rag_time}s rag, {response.llm_time}s llm]")


class TestGraphCreation:
    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_direct_kg_creation(self):
        s = Knwl()
        g = await s.create_kg("""
        Field was born 26 July 1782 in Golden Lane, Dublin, the eldest son of Irish parents who were members of the Church of Ireland. He was baptised on 30 September. His father, Robert Field, earned his living by playing the violin in Dublin theatres. Field first studied the piano under his grandfather (also named John Field), who was a professional organist, and later under Tommaso Giordani. He made his debut at the age of nine, a performance that was well-received, on 24 March 1792 in Dublin. According to an early biographer, W. H. Grattan Flood, Field started composing in Ireland, but no evidence exists to support his claim. Flood also asserted that Field's family moved to Bath, Somerset, in 1793 and lived there for a short time, and this too is considered unlikely by modern researchers. By late 1793, though, the Fields had settled in London, where the young pianist started studying with Muzio Clementi. This arrangement was made possible by Field's father, who was perhaps able to secure the apprenticeship through Giordani, who knew Clementi.

        Field continued giving public performances and soon became famous in London, attracting favourable comments from the press and the local musicians. Around 1795 his performance of a Dussek piano concerto was praised by Haydn. Field continued his studies with Clementi, also helping the Italian with the making and selling of instruments. He also took up violin playing, which he studied under J. P. Solomon. His first published compositions were issued by Clementi in 1795; the first historically important work, Piano Concerto No. 1, H 27, was premiered by the composer in London on 7 February 1799, when he was aged 16. Field's first official opus was a set of three piano sonatas published by (and dedicated to) Clementi in 1801.
        """)
        # print(json.dumps(asdict(g), indent=2))
        g.write_graphml("field.graphml")
        print()
        # print("======================== Timing =====================================")
        # print(f"timing: {g.total_time}s [{g.rag_time}s rag, {g.llm_time}s llm]")


class TestDocuments:
    @pytest.mark.asyncio
    async def test_save_sources_empty(self):
        s = Knwl()
        with pytest.raises(ValueError):
            result = await s.save_sources([])

    @pytest.mark.asyncio
    async def test_save_sources_all_existing(self, mocker):
        s = Knwl()
        sources = [KnwlInput(text="Source 1"), KnwlInput(text="Source 2")]
        mocker.patch.object(s.document_storage, 'filter_new_ids', return_value=[])
        mocker.patch.object(s.document_storage, 'upsert')
        result = await s.save_sources(sources)
        assert result == {}
        s.document_storage.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_sources_new_sources(self, mocker):
        s = Knwl()
        sources = [KnwlInput(text="Source 1"), KnwlInput(text="Source 2")]
        documents = [KnwlDocument.from_input(s) for s in sources]
        new_keys = [d.id for d in documents]
        mocker.patch.object(s.document_storage, 'filter_new_ids', return_value=new_keys)
        mocker.patch.object(s.document_storage, 'upsert')
        result = await s.save_sources(sources)
        assert len(result) == 2
        assert all(key in result for key in new_keys)
        # the following fails because of a small delta in the timestamp
        # s.document_storage.upsert.assert_called_once_with({d.id: asdict(d) for d in documents})


class TestChunks:
    @pytest.mark.asyncio
    async def test_create_chunks_empty_sources(self):
        s = Knwl()
        result = await s.create_chunks({})
        assert result == {}

    @pytest.mark.asyncio
    async def test_create_chunks_all_existing(self, mocker):
        s = Knwl()
        sources = {
            "source1": KnwlDocument(content="Content 1"),
            "source2": KnwlDocument(content="Content 2")
        }
        chunks = {
            hash_with_prefix("Content 1", prefix="chunk-"): {"content": "Content 1", "originId": "source1"},
            hash_with_prefix("Content 2", prefix="chunk-"): {"content": "Content 2", "originId": "source2"}
        }
        mocker.patch.object(s.chunks_storage, 'filter_new_ids', return_value=[])
        mocker.patch.object(s.chunks_storage, 'upsert')
        mocker.patch.object(s.chunk_vectors, 'upsert')
        mocker.patch('knwl.simple.chunk', side_effect=lambda content, key: [KnwlChunk(content=content, originId=key, tokens=len(content.split()))])
        result = await s.create_chunks(sources)
        assert result == {}
        s.chunks_storage.upsert.assert_not_called()
        s.chunk_vectors.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_chunks_new_chunks(self, mocker):
        s = Knwl()
        sources = create_dummy_documents(2)
        # chunks are the same as sources since the content is small
        new_chunks = [KnwlChunk(content=s.content, originId=k, tokens=count_tokens(s.content)) for k, s in sources.items()]
        new_chunk_keys = [c.id for c in new_chunks]
        mocker.patch.object(s.chunks_storage, 'filter_new_ids', return_value=new_chunk_keys)
        mocker.patch.object(s.chunks_storage, 'upsert')
        mocker.patch.object(s.chunk_vectors, 'upsert')
        # mocker.patch('knwl.simple.chunk', side_effect=lambda content, key: [KnwlChunk(content=content, originId=key, tokens=len(content.split()))])
        result = await s.create_chunks(sources)
        assert len(result) == 2
        assert set(new_chunk_keys) == set(result.keys())
        s.chunks_storage.upsert.assert_called_once_with({v.id: asdict(v) for v in new_chunks})
        s.chunk_vectors.upsert.assert_called_once_with({v.id: {"content": v.content, "id": v.id} for v in new_chunks})


class TestGraphMerge:

    @pytest.mark.asyncio
    async def test_merge_nodes_into_graph_no_existing_node(self, mocker):
        s = Knwl()
        entity_name = "entity1"
        nodes = [
            KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name=entity_name),
            KnwlNode(type="Person", description="John lives in Paris.", chunkIds=["chunk2"], name=entity_name)
        ]
        node_id = nodes[0].id
        mocker.patch.object(s.graph_storage, 'get_node_by_id', return_value=None)
        mocker.patch.object(s.graph_storage, 'upsert_node')
        # mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Knwl.compactify_summary', return_value="John is a software engineer. John lives in Paris.")

        result = await s.merge_nodes_into_graph(entity_name, nodes)

        assert result.name == entity_name
        assert result.type == "Person"
        assert result.description == "John is a software engineer. John lives in Paris."
        assert set(result.chunkIds) == {"chunk1", "chunk2"}
        s.graph_storage.upsert_node.assert_called_once_with(node_id, asdict(result))

    @pytest.mark.asyncio
    async def test_merge_nodes_into_graph_existing_node(self, mocker):
        s = Knwl()
        entity_name = "entity1"
        nodes = [
            KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name=entity_name),
            KnwlNode(type="Person", description="John lives in Paris.", chunkIds=["chunk2"], name=entity_name)
        ]
        existing_node = KnwlNode(**{
            "name": entity_name,
            "type": "Person",
            "chunkIds": ["chunk3"],
            "description": "John likes to travel."
        })
        node_id = existing_node.id
        mocker.patch.object(s.graph_storage, 'get_node_by_id', return_value=existing_node)
        mocker.patch.object(s.graph_storage, 'upsert_node')
        mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Knwl.compactify_summary', return_value="John is a software engineer. John lives in Paris. John likes to travel.")

        result = await s.merge_nodes_into_graph(entity_name, nodes)

        assert result.name == entity_name
        assert result.type == "Person"
        assert result.description == "John is a software engineer. John lives in Paris. John likes to travel."
        assert set(result.chunkIds) == {"chunk1", "chunk2", "chunk3"}
        s.graph_storage.upsert_node.assert_called_once_with(node_id, asdict(result))

    @pytest.mark.asyncio
    async def test_merge_nodes_into_graph_different_types(self, mocker):
        s = Knwl()
        entity_name = "entity1"
        nodes = [
            KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name=entity_name),
            KnwlNode(type="Location", description="John lives in Paris.", chunkIds=["chunk2"], name=entity_name)
        ]

        existing_node = KnwlNode(**{
            "name": entity_name,
            "type": "Person",
            "chunkIds": ["chunk3"],
            "description": "John likes to travel."
        })
        node_id = existing_node.id
        mocker.patch.object(s.graph_storage, 'get_node_by_id', return_value=existing_node)
        mocker.patch.object(s.graph_storage, 'upsert_node')
        # mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Knwl.compactify_summary', return_value="John is a software engineer. John lives in Paris. John likes to travel.")

        result = await s.merge_nodes_into_graph(entity_name, nodes)

        assert result.name == entity_name
        assert result.type == "Person"
        assert result.description == "John is a software engineer. John lives in Paris. John likes to travel."
        assert set(result.chunkIds) == {"chunk1", "chunk2", "chunk3"}
        s.graph_storage.upsert_node.assert_called_once_with(node_id, asdict(result))

    @pytest.mark.asyncio
    async def test_compactify_summary_no_smart_merge(self):
        description = f"John is a software engineer.{GRAPH_FIELD_SEP}John lives in Paris."
        result = await Knwl.compactify_summary("John", description, smart_merge=False)
        assert result == "John is a software engineer. John lives in Paris."

    @pytest.mark.asyncio
    async def test_compactify_summary_above_summary_max_tokens(self, mocker):
        description = "John is a software engineer.|John lives in Paris."
        tokens = description.split()
        mocker.patch('knwl.simple.encode', return_value=tokens)
        mocker.patch('knwl.simple.decode', return_value=description)
        mocker.patch('knwl.simple.settings', summary_max=1, max_tokens=len(tokens))
        mocker.patch('knwl.simple.PROMPTS', {"summarize_entity_descriptions": "Summarize: {entity_name} {description_list}"})
        mocker.patch('knwl.simple.Knwl.query', return_value=KnwlResponse(answer="John is a software engineer living in Paris."))
        result = await Knwl.compactify_summary("John", description, smart_merge=True)
        assert result == "John is a software engineer living in Paris." or result == "John is a software engineer who lives in Paris."

    @pytest.mark.asyncio
    async def test_compactify_summary_trigger_summary(self, mocker):
        description = "John is a software engineer.|John lives in Paris.|John likes to travel."
        tokens = description.split()
        mocker.patch('knwl.simple.encode', return_value=tokens)
        mocker.patch('knwl.simple.decode', return_value=description)
        mocker.patch('knwl.simple.settings', summary_max=1, max_tokens=len(tokens))
        mocker.patch('knwl.simple.PROMPTS', {"summarize_entity_descriptions": "Summarize: {entity_name} {description_list}"})
        mocker.patch('knwl.simple.llm.ask', return_value=KnwlLLMAnswer(answer="John is a software engineer living in Paris who likes to travel."))
        result = await Knwl.compactify_summary("John", description, smart_merge=True)
        assert result == "John is a software engineer living in Paris who likes to travel."

    @pytest.mark.asyncio
    async def test_merge_edges_into_graph_no_existing_edge(self, mocker):
        s = Knwl()
        edge_id = "(source1,target1)"
        edges = [
            KnwlEdge(weight=1.0, sourceId="source1", targetId="target1", description="Edge 1", keywords=["keyword1"], chunkIds=["chunk1"]),
            KnwlEdge(weight=2.0, sourceId="source1", targetId="target1", description="Edge 2", keywords=["keyword2"], chunkIds=["chunk2"])
        ]

        mocker.patch.object(s.graph_storage, 'edge_exists', return_value=False)
        mocker.patch.object(s.graph_storage, 'upsert_edge')
        mocker.patch.object(s.graph_storage, 'node_exists', return_value=True)
        mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Knwl.compactify_summary', return_value="Edge 1 Edge 2")

        result = await s.merge_edges_into_graph(edges)

        assert result.sourceId == "source1"
        assert result.targetId == "target1"
        assert result.weight == 3.0
        assert result.description == "Edge 1 Edge 2"
        assert set(result.keywords) == {"keyword1", "keyword2"}
        assert set(result.chunkIds) == {"chunk1", "chunk2"}
        s.graph_storage.upsert_edge.assert_called_once_with("source1", "target1", result)

    @pytest.mark.asyncio
    async def test_merge_edges_into_graph_existing_edge(self, mocker):
        s = Knwl()
        edges = [
            KnwlEdge(weight=1.0, sourceId="source1", targetId="target1", description="Edge 1", keywords=["keyword1"], chunkIds=["chunk1"]),
            KnwlEdge(weight=2.0, sourceId="source1", targetId="target1", description="Edge 2", keywords=["keyword2"], chunkIds=["chunk2"])
        ]
        existing_edge = KnwlEdge(**{
            "sourceId": "source1",
            "targetId": "target1",
            "weight": 1.5,
            "chunkIds": ["chunk3"],
            "description": "Existing edge",
            "keywords": ["existing_keyword"]
        })

        mocker.patch.object(s.graph_storage, 'edge_exists', return_value=True)
        mocker.patch.object(s.graph_storage, 'get_edge', return_value=existing_edge)
        mocker.patch.object(s.graph_storage, 'upsert_edge')
        mocker.patch.object(s.graph_storage, 'node_exists', return_value=True)
        mocker.patch('knwl.simple.Knwl.compactify_summary', return_value="Edge 1 Edge 2 Existing edge")

        result = await s.merge_edges_into_graph(edges)

        assert result.sourceId == "source1"
        assert result.targetId == "target1"
        assert result.weight == 4.5
        assert result.description == "Edge 1 Edge 2 Existing edge"
        assert set(result.keywords) == {"keyword1", "keyword2", "existing_keyword"}
        assert set(result.chunkIds) == {"chunk1", "chunk2", "chunk3"}
        s.graph_storage.upsert_edge.assert_called_once_with("source1", "target1", result)

    @pytest.mark.asyncio
    async def test_merge_edges_into_graph_missing_nodes(self, mocker):
        s = Knwl()
        edge_id = "(source1,target1)"
        edges = [
            KnwlEdge(weight=1.0, sourceId="source1", targetId="target1", description="Edge 1", keywords=["keyword1"], chunkIds=["chunk1"]),
            KnwlEdge(weight=2.0, sourceId="source1", targetId="target1", description="Edge 2", keywords=["keyword2"], chunkIds=["chunk2"])
        ]

        mocker.patch.object(s.graph_storage, 'edge_exists', return_value=False)
        mocker.patch.object(s.graph_storage, 'upsert_edge')
        mocker.patch.object(s.graph_storage, 'node_exists', side_effect=[False, False])
        mocker.patch.object(s.graph_storage, 'upsert_node')
        mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Knwl.compactify_summary', return_value="Edge 1 Edge 2")

        with pytest.raises(ValueError):
            result = await s.merge_edges_into_graph(edges)

    @pytest.mark.asyncio
    async def test_merge_extraction_into_knowledge_graph_no_nodes_or_edges(self, mocker):
        s = Knwl()
        extraction = KnwlExtraction(nodes={}, edges={})

        mocker.patch.object(s, 'merge_nodes_into_graph', return_value=None)
        mocker.patch.object(s, 'merge_edges_into_graph', return_value=None)

        result = await s.merge_extraction_into_knowledge_graph(extraction)

        assert result.nodes == []
        assert result.edges == []

    @pytest.mark.asyncio
    async def test_merge_extraction_into_knowledge_graph_with_multiple_nodes_and_edges(self, mocker):
        s = Knwl()
        node1 = KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name="entity1")
        node2 = KnwlNode(type="Location", description="Paris is a city.", chunkIds=["chunk2"], name="entity2")
        edge1 = KnwlEdge(weight=1.0, sourceId=node1.id, targetId=node2.id, description="Edge 1", keywords=["keyword1"], chunkIds=["chunk1"])
        edge2 = KnwlEdge(weight=2.0, sourceId=node1.id, targetId=node2.id, description="Edge 2", keywords=["keyword2"], chunkIds=["chunk2"])
        merged_edge = KnwlEdge(weight=3.0, sourceId=node1.id, targetId=node2.id, description="Edge 1 Edge 2", keywords=["keyword1", "keyword2"], chunkIds=["chunk1", "chunk2"])
        extraction = KnwlExtraction(
            nodes={
                node1.name: [node1],
                node2.name: [node2]
            },
            edges={
                "(entity1,entity2)": [edge1, edge2],
            }
        )

        mocker.patch.object(s, 'merge_nodes_into_graph', side_effect=[node1, node2])
        mocker.patch.object(s, 'merge_edges_into_graph', side_effect=[merged_edge])

        result = await s.merge_extraction_into_knowledge_graph(extraction)

        assert len(result.nodes) == 2
        assert result.nodes[0].id == node1.id
        assert result.nodes[1].id == node2.id
        assert len(result.edges) == 1
        assert result.edges[0].id == merged_edge.id


class TestQuery:
    @pytest.mark.asyncio
    async def test_get_local_query_context_no_results(self, mocker):
        s = Knwl()
        query = "test query"
        query_param = QueryParam(top_k=5)

        mocker.patch.object(s.node_vectors, 'query', return_value=[])
        result = await s.get_local_query_context(query, query_param)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_primary_nodes_no_results(self, mocker):
        s = Knwl()
        query = "test query"
        query_param = QueryParam(top_k=5)

        mocker.patch.object(s.node_vectors, 'query', return_value=[])
        result = await s.get_primary_nodes(query, query_param)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_primary_nodes_some_missing_nodes(self, mocker):
        s = Knwl()
        query = "test query"
        query_param = QueryParam(top_k=5)
        found = [{"name": "node1", "id": "node1"}, {"name": "node2", "id": "node2"}]
        node_datas = [KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1"]), None]
        node_degrees = [3, 2]

        mocker.patch.object(s.node_vectors, 'query', return_value=found)
        mocker.patch.object(s.graph_storage, 'get_node_by_id', side_effect=node_datas)
        mocker.patch.object(s.graph_storage, 'node_degree', side_effect=node_degrees)
        mocker.patch('knwl.simple.logger.warning')

        result = await s.get_primary_nodes(query, query_param)

        assert len(result) == 1
        assert result[0].name == "node1"
        assert result[0].degree == 3
        knwl.knwl.logger.warning.assert_called_once_with("Some nodes are missing, maybe the storage is damaged")

    @pytest.mark.asyncio
    async def test_get_primary_nodes_all_nodes_present(self, mocker):
        s = Knwl()
        query = "test query"
        query_param = QueryParam(top_k=5)
        found = [{"name": "node1", "id": "node1"}, {"name": "node2", "id": "node2"}]
        node_datas = [
            KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1"]),
            KnwlNode(name="node2", type="Location", description="Description 2", chunkIds=["chunk2"])
        ]
        node_degrees = [3, 2]

        mocker.patch.object(s.node_vectors, 'query', return_value=found)
        mocker.patch.object(s.graph_storage, 'get_node_by_id', side_effect=node_datas)
        mocker.patch.object(s.graph_storage, 'node_degree', side_effect=node_degrees)

        result = await s.get_primary_nodes(query, query_param)

        assert len(result) == 2
        assert result[0].name == "node1"
        assert result[0].degree == 3
        assert result[1].name == "node2"
        assert result[1].degree == 2

    @pytest.mark.asyncio
    async def test_get_attached_edges_no_nodes(self):
        s = Knwl()
        result = await s.get_attached_edges([])
        assert result == []

    @pytest.mark.asyncio
    async def test_get_attached_edges_with_nodes(self, mocker):
        s = Knwl()
        query_param = QueryParam()
        nodes = [
            KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1"]),
            KnwlNode(name="node2", type="Location", description="Description 2", chunkIds=["chunk2"])
        ]
        edges = [
            KnwlEdge(weight=1.1, sourceId="node1", targetId="node2", description="Edge 1", keywords="keyword1", chunkIds=["chunk1"]),
            KnwlEdge(weight=2.2, sourceId="node2", targetId="node4", description="Edge 2", keywords="keyword2", chunkIds=["chunk2"]),
            KnwlEdge(weight=3.3, sourceId="node2", targetId="node6", description="Edge 3", keywords="keyword2", chunkIds=["chunk43"])
        ]

        mocker.patch.object(s.graph_storage, 'get_node_edges', return_value=edges)

        result = await s.get_attached_edges(nodes)

        assert len(result) == 3
        assert result[0].sourceId == "node1"
        assert result[0].targetId == "node2"
        assert result[1].sourceId == "node2"
        assert result[1].targetId == "node4"

    @pytest.mark.asyncio
    async def test_get_attached_edges_some_missing_edges(self, mocker):
        s = Knwl()
        query_param = QueryParam()
        nodes = [
            KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1"]),
            KnwlNode(name="node2", type="Location", description="Description 2", chunkIds=["chunk2"])
        ]
        edges = [
            [KnwlEdge(weight=1.0, sourceId="node1", targetId="node2", description="Edge 1", keywords="keyword1", chunkIds=["chunk1"])],
            [KnwlEdge(weight=1.3, sourceId="node1", targetId="node3", description="Edge 2", keywords="keyword1", chunkIds=["chunk1"])],
            [KnwlEdge(weight=1.3, sourceId="node1", targetId="node3", description="Edge 2", keywords="keyword1", chunkIds=["chunk1"])]  # duplicate edge by intention
        ]

        mocker.patch.object(s.graph_storage, 'get_node_edges', side_effect=edges)

        result = await s.get_attached_edges(nodes)

        assert len(result) == 2

        assert result[0].sourceId == "node1"
        assert result[0].targetId == "node2"
        assert result[1].sourceId == "node1"
        assert result[1].targetId == "node3"

    @pytest.mark.asyncio
    @pytest.mark.llm
    async def test_basic_rag(self):
        doc1 = "John is a software engineer and he is 34 years old."
        doc2 = "The QZ3 theory is about quantum topology and it is a new approach to quantum mechanics."
        doc3 = "The z1-function computes the inverse Riemann zeta function."
        s = Knwl()

        await s.insert([doc1, doc2, doc3], basic_rag=True)
        assert await s.count_documents() == 3

        response = await s.query("Who is John?", QueryParam(mode="naive"))
        assert response is not None
        print()
        print(response.answer)  # something like: John is a software engineer who is 34 years old. No other specific details about him are provided in the given information.
        assert "John is a software engineer" in response.answer

        response = await s.query("What is z1?", QueryParam(mode="naive"))
        assert response is not None
        print()
        print(response.answer)
        assert "inverse of the Riemann zeta function" in response.answer


class TestChunkStats:
    @pytest.mark.asyncio
    async def test_create_chunk_stats_no_primary_nodes(self):
        s = Knwl()
        result = await s.create_chunk_stats_from_nodes([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_create_chunk_stats_no_edges(self, mocker):
        s = Knwl()
        primary_nodes = [
            KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1"]),
            KnwlNode(name="node2", type="Location", description="Description 2", chunkIds=["chunk2"])
        ]

        mocker.patch.object(s, 'get_attached_edges', return_value=[])
        result = await s.create_chunk_stats_from_nodes(primary_nodes)
        assert result == {"chunk1": 0, "chunk2": 0}

    @pytest.mark.asyncio
    async def test_create_chunk_stats_with_edges(self, mocker):
        s = Knwl()
        # primary nodes: node1, node2 found in chunk1
        # (3)--(1)--(2)
        # (4)_/

        node1 = KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1", "chunk3", "chunk4"])
        node2 = KnwlNode(name="node2", type="Location", description="Description 2", chunkIds=["chunk1"])
        node3 = KnwlNode(name="node3", type="Location", description="Description 3", chunkIds=["chunk1", "chunk3"])
        node4 = KnwlNode(name="node4", type="Something", description="Description 4", chunkIds=["chunk4"])

        edge12 = KnwlEdge(weight=1.0, sourceId=node1.id, targetId=node2.id, description="Edge 12", keywords=["keyword1"], chunkIds=["chunk1"])
        edge13 = KnwlEdge(weight=1.0, sourceId=node1.id, targetId=node3.id, description="Edge 13", keywords=["keyword1"], chunkIds=["chunk3"])
        edge14 = KnwlEdge(weight=1.0, sourceId=node1.id, targetId=node4.id, description="Edge 14", keywords=["keyword1"], chunkIds=["chunk4"])

        primary_nodes = [node1, node2]

        def get_node_by_id(id: str):
            if id == node1.id:
                return node1
            if id == node2.id:
                return node2
            if id == node3.id:
                return node3
            if id == node4.id:
                return node4
            raise ValueError(f"Unknown node obj: {id}")

        def get_attached_edges(obj: List[KnwlNode] | str):

            if isinstance(obj, List):
                found = [get_attached_edges(x.id) for x in obj]
                # flatten the list
                found = [item for sublist in found for item in sublist]
                # make unique
                unique_ids = set([e.id for e in found])
                return [e for e in found if e.id in unique_ids]

            if obj == node1.id:
                return [edge12, edge13, edge14]
            if obj == node2.id:
                return [edge12]
            if obj == node3.id:
                return [edge13]
            if obj == node4.id:
                return [edge14]
            raise ValueError(f"Unknown node obj: {obj}")

        mocker.patch.object(s, 'get_attached_edges', side_effect=get_attached_edges)
        mocker.patch.object(s.graph_storage, 'get_node_by_id', side_effect=get_node_by_id)

        result = await s.create_chunk_stats_from_nodes(primary_nodes)
        assert result == {"chunk1": 2, "chunk3": 1, "chunk4": 1}

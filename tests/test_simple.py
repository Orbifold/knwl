from dataclasses import asdict
from typing import List

import pytest

import knwl
from knwl.prompt import GRAPH_FIELD_SEP
from knwl.simple import Simple
from knwl.utils import KnwlExtraction, KnwlNode, KnwlDocument, hash_with_prefix, KnwlChunk, KnwlEdge, QueryParam
from faker import Faker

faker = Faker()


def create_dummy_sources(n=10):
    sources = {}
    for i in range(n):
        source = KnwlDocument(content=faker.text(), name=faker.catch_phrase(), description=faker.sentence())
        sources[hash_with_prefix(source.content, prefix="doc-")] = source
    return sources


class TestRealCases:

    @pytest.mark.asyncio
    async def test_query_local(self):
        s = Simple()
        await s.input('John is married to Anna.', "Married")
        await s.input('Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.', "Family")
        await s.input('John has been working for the past ten years on AI and robotics. He knows a lot about the subject.', "Work")
        response = await s.query("Who is John?", QueryParam(mode="local"))
        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)
        print()
        print("======================== References =====================================")
        print(response.context.get_references_table())

    @pytest.mark.asyncio
    async def test_global_local(self):
        s = Simple()
        await s.insert('John is married to Anna.')
        await s.insert('Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.')
        await s.insert('John has been working for the past ten years on AI and robotics. He knows a lot about the subject.')
        response = await s.query("Who is John?", QueryParam(mode="global"))
        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)

    @pytest.mark.asyncio
    async def test_naive_local(self):
        s = Simple()
        await s.insert('John is married to Anna.')
        await s.insert('Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.')
        await s.insert('John has been working for the past ten years on AI and robotics. He knows a lot about the subject.')
        response = await s.query("Who is John?", QueryParam(mode="naive"))
        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)

    @pytest.mark.asyncio
    async def test_hybrid_local(self):
        s = Simple()
        await s.insert('John is married to Anna.')
        await s.insert('Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.')
        await s.insert('John has been working for the past ten years on AI and robotics. He knows a lot about the subject.')
        response = await s.query("Who is John?", QueryParam(mode="hybrid"))
        print()
        print("======================== Context ====================================")
        print(response.context)
        print("======================== Answer =====================================")
        print(response.answer)


class TestDocuments:
    @pytest.mark.asyncio
    async def test_save_sources_empty(self):
        s = Simple()
        result = await s.save_sources([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_save_sources_all_existing(self, mocker):
        s = Simple()
        sources = ["Source 1", "Source 2"]
        mocker.patch.object(s.document_storage, 'filter_new_ids', return_value=[])
        mocker.patch.object(s.document_storage, 'upsert')
        result = await s.save_sources(sources)
        assert result == {}
        s.document_storage.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_sources_new_sources(self, mocker):
        s = Simple()
        sources = ["Source 1", "Source 2"]
        new_keys = [hash_with_prefix("Source 1", prefix="doc-"), hash_with_prefix("Source 2", prefix="doc-")]
        mocker.patch.object(s.document_storage, 'filter_new_ids', return_value=new_keys)
        mocker.patch.object(s.document_storage, 'upsert')
        result = await s.save_sources(sources)
        assert len(result) == 2
        assert all(key in result for key in new_keys)
        s.document_storage.upsert.assert_called_once_with(result)


class TestChunks:
    @pytest.mark.asyncio
    async def test_create_chunks_empty_sources(self):
        s = Simple()
        result = await s.create_chunks({})
        assert result == {}

    @pytest.mark.asyncio
    async def test_create_chunks_all_existing(self, mocker):
        s = Simple()
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
        s = Simple()
        sources = create_dummy_sources(2)
        # chunks are the same as sources since the content is small
        new_chunk_keys = [hash_with_prefix(s.content, prefix="chunk-") for k, s in sources.items()]
        mocker.patch.object(s.chunks_storage, 'filter_new_ids', return_value=new_chunk_keys)
        mocker.patch.object(s.chunks_storage, 'upsert')
        mocker.patch.object(s.chunk_vectors, 'upsert')
        mocker.patch('knwl.simple.chunk', side_effect=lambda content, key: [KnwlChunk(content=content, originId=key, tokens=len(content.split()))])
        result = await s.create_chunks(sources)
        assert len(result) == 2
        assert all(key in result for key in new_chunk_keys)
        s.chunks_storage.upsert.assert_called_once_with(result)
        s.chunk_vectors.upsert.assert_called_once_with({k: {"content": v.content} for k, v in result.items()})


class TestGraphMerge:

    @pytest.mark.asyncio
    async def test_merge_nodes_into_graph_no_existing_node(self, mocker):
        s = Simple()
        entity_id = "entity1"
        nodes = [
            KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name=entity_id),
            KnwlNode(type="Person", description="John lives in Paris.", chunkIds=["chunk2"], name=entity_id)
        ]

        mocker.patch.object(s.graph_storage, 'get_node_by_id', return_value=None)
        mocker.patch.object(s.graph_storage, 'upsert_node')
        # mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Simple.compactify_summary', return_value="John is a software engineer. John lives in Paris.")

        result = await s.merge_nodes_into_graph(entity_id, nodes)

        assert result.name == entity_id
        assert result.type == "Person"
        assert result.description == "John is a software engineer. John lives in Paris."
        assert set(result.chunkIds) == {"chunk1", "chunk2"}
        s.graph_storage.upsert_node.assert_called_once_with(entity_id, asdict(result))

    @pytest.mark.asyncio
    async def test_merge_nodes_into_graph_existing_node(self, mocker):
        s = Simple()
        entity_id = "entity1"
        nodes = [
            KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name=entity_id),
            KnwlNode(type="Person", description="John lives in Paris.", chunkIds=["chunk2"], name=entity_id)
        ]
        existing_node = KnwlNode(**{
            "name": entity_id,
            "type": "Person",
            "chunkIds": ["chunk3"],
            "description": "John likes to travel."
        })

        mocker.patch.object(s.graph_storage, 'get_node_by_id', return_value=existing_node)
        mocker.patch.object(s.graph_storage, 'upsert_node')
        mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Simple.compactify_summary', return_value="John is a software engineer. John lives in Paris. John likes to travel.")

        result = await s.merge_nodes_into_graph(entity_id, nodes)

        assert result.name == entity_id
        assert result.type == "Person"
        assert result.description == "John is a software engineer. John lives in Paris. John likes to travel."
        assert set(result.chunkIds) == {"chunk1", "chunk2", "chunk3"}
        s.graph_storage.upsert_node.assert_called_once_with(entity_id, asdict(result))

    @pytest.mark.asyncio
    async def test_merge_nodes_into_graph_different_types(self, mocker):
        s = Simple()
        entity_id = "entity1"
        nodes = [
            KnwlNode(type="Person", description="John is a software engineer.", chunkIds=["chunk1"], name=entity_id),
            KnwlNode(type="Location", description="John lives in Paris.", chunkIds=["chunk2"], name=entity_id)
        ]
        existing_node = KnwlNode(**{
            "name": entity_id,
            "type": "Person",
            "chunkIds": ["chunk3"],
            "description": "John likes to travel."
        })

        mocker.patch.object(s.graph_storage, 'get_node_by_id', return_value=existing_node)
        mocker.patch.object(s.graph_storage, 'upsert_node')
        # mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Simple.compactify_summary', return_value="John is a software engineer. John lives in Paris. John likes to travel.")

        result = await s.merge_nodes_into_graph(entity_id, nodes)

        assert result.name == entity_id
        assert result.type == "Person"
        assert result.description == "John is a software engineer. John lives in Paris. John likes to travel."
        assert set(result.chunkIds) == {"chunk1", "chunk2", "chunk3"}
        s.graph_storage.upsert_node.assert_called_once_with(entity_id, asdict(result))

    @pytest.mark.asyncio
    async def test_compactify_summary_no_smart_merge(self):
        description = f"John is a software engineer.{GRAPH_FIELD_SEP}John lives in Paris."
        result = await Simple.compactify_summary("John", description, smart_merge=False)
        assert result == "John is a software engineer. John lives in Paris."

    @pytest.mark.asyncio
    async def test_compactify_summary_above_summary_max_tokens(self, mocker):
        description = "John is a software engineer.|John lives in Paris."
        tokens = description.split()
        mocker.patch('knwl.simple.encode', return_value=tokens)
        mocker.patch('knwl.simple.decode', return_value=description)
        mocker.patch('knwl.simple.settings', summary_max=1, max_tokens=len(tokens))
        mocker.patch('knwl.simple.PROMPTS', {"summarize_entity_descriptions": "Summarize: {entity_name} {description_list}"})
        mocker.patch('knwl.simple.ollama_chat', return_value="John is a software engineer living in Paris.")
        result = await Simple.compactify_summary("John", description, smart_merge=True)
        assert result == "John is a software engineer living in Paris."

    @pytest.mark.asyncio
    async def test_compactify_summary_trigger_summary(self, mocker):
        description = "John is a software engineer.|John lives in Paris.|John likes to travel."
        tokens = description.split()
        mocker.patch('knwl.simple.encode', return_value=tokens)
        mocker.patch('knwl.simple.decode', return_value=description)
        mocker.patch('knwl.simple.settings', summary_max=1, max_tokens=len(tokens))
        mocker.patch('knwl.simple.PROMPTS', {"summarize_entity_descriptions": "Summarize: {entity_name} {description_list}"})
        mocker.patch('knwl.simple.ollama_chat', return_value="John is a software engineer living in Paris who likes to travel.")
        result = await Simple.compactify_summary("John", description, smart_merge=True)
        assert result == "John is a software engineer living in Paris who likes to travel."

    @pytest.mark.asyncio
    async def test_merge_edges_into_graph_no_existing_edge(self, mocker):
        s = Simple()
        edge_id = "(source1,target1)"
        edges = [
            KnwlEdge(weight=1.0, sourceId="source1", targetId="target1", description="Edge 1", keywords=["keyword1"], chunkIds=["chunk1"]),
            KnwlEdge(weight=2.0, sourceId="source1", targetId="target1", description="Edge 2", keywords=["keyword2"], chunkIds=["chunk2"])
        ]

        mocker.patch.object(s.graph_storage, 'edge_exists', return_value=False)
        mocker.patch.object(s.graph_storage, 'upsert_edge')
        mocker.patch.object(s.graph_storage, 'node_exists', return_value=True)
        mocker.patch('knwl.simple.split_string_by_multi_markers', side_effect=lambda x, y: x.split(y[0]))
        mocker.patch('knwl.simple.Simple.compactify_summary', return_value="Edge 1 Edge 2")

        result = await s.merge_edges_into_graph(edge_id, edges)

        assert result.sourceId == "source1"
        assert result.targetId == "target1"
        assert result.weight == 3.0
        assert result.description == "Edge 1 Edge 2"
        assert set(result.keywords) == {"keyword1", "keyword2"}
        assert set(result.chunkIds) == {"chunk1", "chunk2"}
        s.graph_storage.upsert_edge.assert_called_once_with("source1", "target1", result)

    @pytest.mark.asyncio
    async def test_merge_edges_into_graph_existing_edge(self, mocker):
        s = Simple()
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
        mocker.patch('knwl.simple.Simple.compactify_summary', return_value="Edge 1 Edge 2 Existing edge")

        result = await s.merge_edges_into_graph("(source1,target1)", edges)

        assert result.sourceId == "source1"
        assert result.targetId == "target1"
        assert result.weight == 4.5
        assert result.description == "Edge 1 Edge 2 Existing edge"
        assert set(result.keywords) == {"keyword1", "keyword2", "existing_keyword"}
        assert set(result.chunkIds) == {"chunk1", "chunk2", "chunk3"}
        s.graph_storage.upsert_edge.assert_called_once_with("source1", "target1", result)

    @pytest.mark.asyncio
    async def test_merge_edges_into_graph_missing_nodes(self, mocker):
        s = Simple()
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
        mocker.patch('knwl.simple.Simple.compactify_summary', return_value="Edge 1 Edge 2")

        with pytest.raises(ValueError):
            result = await s.merge_edges_into_graph(edge_id, edges)

    @pytest.mark.asyncio
    async def test_merge_extraction_into_knowledge_graph_no_nodes_or_edges(self, mocker):
        s = Simple()
        extraction = KnwlExtraction(nodes={}, edges={})

        mocker.patch.object(s, 'merge_nodes_into_graph', return_value=None)
        mocker.patch.object(s, 'merge_edges_into_graph', return_value=None)

        result = await s.merge_extraction_into_knowledge_graph(extraction)

        assert result.nodes == []
        assert result.edges == []

    @pytest.mark.asyncio
    async def test_merge_extraction_into_knowledge_graph_with_multiple_nodes_and_edges(self, mocker):
        s = Simple()
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
        s = Simple()
        query = "test query"
        query_param = QueryParam(top_k=5)

        mocker.patch.object(s.node_vectors, 'query', return_value=[])
        result = await s.get_local_query_context(query, query_param)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_primary_nodes_no_results(self, mocker):
        s = Simple()
        query = "test query"
        query_param = QueryParam(top_k=5)

        mocker.patch.object(s.node_vectors, 'query', return_value=[])
        result = await s.get_primary_nodes(query, query_param)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_primary_nodes_some_missing_nodes(self, mocker):
        s = Simple()
        query = "test query"
        query_param = QueryParam(top_k=5)
        found = [{"name": "node1"}, {"name": "node2"}]
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
        knwl.simple.logger.warning.assert_called_once_with("Some nodes are missing, maybe the storage is damaged")

    @pytest.mark.asyncio
    async def test_get_primary_nodes_all_nodes_present(self, mocker):
        s = Simple()
        query = "test query"
        query_param = QueryParam(top_k=5)
        found = [{"name": "node1"}, {"name": "node2"}]
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
        s = Simple()
        result = await s.get_attached_edges([])
        assert result == []

    @pytest.mark.asyncio
    async def test_get_attached_edges_with_nodes(self, mocker):
        s = Simple()
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
        s = Simple()
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
    async def test_basic_rag(self):
        doc1 = "John is a software engineer and he is 34 years old."
        doc2 = "The QZ3 theory is about quantum topology and it is a new approach to quantum mechanics."
        doc3 = "The z1-function computes the inverse Riemann zeta function."
        s = Simple()

        await s.insert([doc1, doc2, doc3], basic_rag=True)
        assert await s.count_documents() == 3

        answer = await s.query("Who is John?", QueryParam(mode="naive"))
        assert answer is not None
        print()
        print(answer)  # something like: John is a software engineer who is 34 years old. No other specific details about him are provided in the given information.
        assert "John is a software engineer" in answer

        answer = await s.query("What is z1?", QueryParam(mode="naive"))
        assert answer is not None
        print()
        print(answer)
        assert "inverse of the Riemann zeta function" in answer


class TestChunkStats:
    @pytest.mark.asyncio
    async def test_create_chunk_stats_no_primary_nodes(self):
        s = Simple()
        result = await s.create_chunk_stats_from_nodes([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_create_chunk_stats_no_edges(self, mocker):
        s = Simple()
        primary_nodes = [
            KnwlNode(name="node1", type="Person", description="Description 1", chunkIds=["chunk1"]),
            KnwlNode(name="node2", type="Location", description="Description 2", chunkIds=["chunk2"])
        ]

        mocker.patch.object(s, 'get_attached_edges', return_value=[])
        result = await s.create_chunk_stats_from_nodes(primary_nodes)
        assert result == {"chunk1": 0, "chunk2": 0}

    @pytest.mark.asyncio
    async def test_create_chunk_stats_with_edges(self, mocker):
        s = Simple()
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

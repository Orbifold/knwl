import asyncio
import json
from hashlib import md5

import pytest

from knwl.settings import settings
from knwl.utils import clean_str, pack_messages, split_string_by_multi_markers, KnwlDocument, KnwlChunk, hash_with_prefix, KnwlNode, KnwlEdge, KnwlContext, KnwlRagChunk, KnwlRagNode, KnwlRagEdge
from knwl.utils import (
    hash_args,
    get_json_body,
    convert_response_to_json,
)
from knwl.utils import throttle


def test_valid_json_string():
    content = 'Some text before {"key": "value"} some text after'
    expected = '{"key": "value"}'
    result = get_json_body(content)
    assert result == expected


def test_no_json_string():
    content = "Some text without JSON"
    result = get_json_body(content)
    assert result is None


def test_empty_string():
    content = ""
    result = get_json_body(content)
    assert result is None


def test_multiple_json_strings():
    content = 'First JSON: {"key1": "value1"} Second JSON: {"key2": "value2"}'
    expected = '{"key1": "value1"}'
    result = get_json_body(content)
    assert result == expected


def test_json_string_with_nested_objects():
    content = 'Text with nested JSON: {"key": {"nested_key": "nested_value"}}'
    expected = '{"key": {"nested_key": "nested_value"}}'
    result = get_json_body(content)
    assert result == expected


def test_null_input():
    with pytest.raises(ValueError):
        get_json_body(None)


def test_convert_response_to_json_valid():
    response = 'Some text before {"key": "value"} some text after'
    expected = {"key": "value"}
    result = convert_response_to_json(response)
    assert result == expected


def test_convert_response_to_json_no_json():
    response = "Some text without JSON"
    with pytest.raises(AssertionError):
        convert_response_to_json(response)


def test_convert_response_to_json_invalid_json():
    response = 'Some text before {"key": "value" some text after'
    with pytest.raises(json.JSONDecodeError):
        convert_response_to_json(response)


def test_convert_response_to_json_multiple_json():
    response = 'First JSON: {"key1": "value1"} Second JSON: {"key2": "value2"}'
    expected = {"key1": "value1"}
    result = convert_response_to_json(response)
    assert result == expected


def test_convert_response_to_json_nested_json():
    response = 'Text with nested JSON: {"key": {"nested_key": "nested_value"}}'
    expected = {"key": {"nested_key": "nested_value"}}
    result = convert_response_to_json(response)
    assert result == expected


def test_compute_args_hash_single_arg():
    arg = "test"
    expected = md5(str((arg,)).encode()).hexdigest()
    result = hash_args(arg)
    assert result == expected


def test_compute_args_hash_multiple_args():
    args = ("test1", "test2", 123)
    expected = md5(str(args).encode()).hexdigest()
    result = hash_args(*args)
    assert result == expected


def test_compute_args_hash_no_args():
    expected = md5(str(()).encode()).hexdigest()
    result = hash_args()
    assert result == expected


def test_compute_args_hash_same_args_different_order():
    args1 = ("test1", "test2")
    args2 = ("test2", "test1")
    result1 = hash_args(*args1)
    result2 = hash_args(*args2)
    assert result1 != result2


def test_compute_args_hash_with_none():
    args = (None, "test")
    expected = md5(str(args).encode()).hexdigest()
    result = hash_args(*args)
    assert result == expected


def test_settings_update():
    settings.update(tokenize_size=100, tokenize_overlap=10)
    assert settings.tokenize_size == 100
    assert settings.tokenize_overlap == 10


def test_clean_str_html_escape():
    input_str = "Hello &amp; welcome!"
    expected = "Hello & welcome!"
    result = clean_str(input_str)
    assert result == expected


def test_clean_str_control_characters():
    input_str = "Hello\x00World\x1f!"
    expected = "HelloWorld!"
    result = clean_str(input_str)
    assert result == expected


def test_clean_str_non_string_input():
    input_data = 12345
    result = clean_str(input_data)
    assert result == input_data


def test_clean_str_empty_string():
    input_str = ""
    expected = ""
    result = clean_str(input_str)
    assert result == expected


def test_clean_str_whitespace():
    input_str = "   Hello World!   "
    expected = "Hello World!"
    result = clean_str(input_str)
    assert result == expected


def test_split_string_by_multi_markers_single_marker():
    content = "Hello, world! This is a test."
    markers = [","]
    expected = ["Hello", "world! This is a test."]
    result = split_string_by_multi_markers(content, markers)
    assert result == expected


def test_split_string_by_multi_markers_multiple_markers():
    content = "Hello, world! This is a test."
    markers = [",", "!"]
    expected = ["Hello", "world", "This is a test."]
    result = split_string_by_multi_markers(content, markers)
    assert result == expected


def test_split_string_by_multi_markers_no_markers():
    content = "Hello, world! This is a test."
    markers = []
    expected = ["Hello, world! This is a test."]
    result = split_string_by_multi_markers(content, markers)
    assert result == expected


def test_split_string_by_multi_markers_empty_content():
    content = ""
    markers = [","]
    expected = [""]
    result = split_string_by_multi_markers(content, markers)
    assert result == expected


def test_split_string_by_multi_markers_no_content():
    content = None
    markers = [","]
    with pytest.raises(TypeError):
        split_string_by_multi_markers(content, markers)


def test_split_string_by_multi_markers_whitespace():
    content = "   Hello, world!   "
    markers = [","]
    expected = ["Hello", "world!"]
    result = split_string_by_multi_markers(content, markers)
    assert result == expected


def test_split_string_by_multi_markers_consecutive_markers():
    content = "Hello,, world!! This is a test."
    markers = [",", "!"]
    expected = ["Hello", "world", "This is a test."]
    result = split_string_by_multi_markers(content, markers)
    assert result == expected


def test_pack_messages_single_message():
    messages = ("Hello",)
    expected = [{"role": "user", "content": "Hello"}]
    result = pack_messages(*messages)
    assert result == expected


def test_pack_messages_multiple_messages():
    messages = ("Hello", "Hi", "How are you?")
    expected = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "How are you?"},
    ]
    result = pack_messages(*messages)
    assert result == expected


def test_pack_messages_no_messages():
    messages = ()
    expected = []
    result = pack_messages(*messages)
    assert result == expected


def test_pack_messages_alternating_roles():
    messages = ("Message 1", "Message 2", "Message 3", "Message 4")
    expected = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Message 2"},
        {"role": "user", "content": "Message 3"},
        {"role": "assistant", "content": "Message 4"},
    ]
    result = pack_messages(*messages)
    assert result == expected


def test_pack_messages_empty_string():
    messages = ("",)
    expected = [{"role": "user", "content": ""}]
    result = pack_messages(*messages)
    assert result == expected


@pytest.mark.asyncio
async def test_limit_async_func_call_single_call():
    @throttle(max_size=1)
    async def sample_func(x):
        return x

    result = await sample_func(5)
    assert result == 5


@pytest.mark.asyncio
async def test_limit_async_func_call_multiple_calls():
    @throttle(max_size=2)
    async def sample_func(x):
        await asyncio.sleep(0.1)
        return x

    tasks = [sample_func(i) for i in range(4)]
    results = await asyncio.gather(*tasks)
    assert results == [0, 1, 2, 3]


@pytest.mark.skip("Not relevant for the current implementation")
@pytest.mark.asyncio
async def test_limit_async_func_call_exceeding_limit():
    @throttle(max_size=2, waitting_time=0.01)
    async def sample_func(x):
        await asyncio.sleep(0.1)
        return x

    tasks = [sample_func(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    assert results == list(range(100))


@pytest.mark.asyncio
async def test_limit_async_func_call_with_waiting():
    @throttle(max_size=1, waitting_time=0.01)
    async def sample_func(x):
        await asyncio.sleep(0.1)
        return x

    tasks = [sample_func(i) for i in range(2)]
    results = await asyncio.gather(*tasks)
    assert results == [0, 1]


def test_source():
    source = KnwlDocument(content="Hello, world!")
    assert source.content == "Hello, world!"
    assert source.id is not None
    print()
    print(source)

    print()
    print(source.__dict__)
    with pytest.raises(AttributeError):
        source.content = "New content"


def test_chunk_class():
    with pytest.raises(ValueError):
        KnwlChunk(content="", tokens=2, index=0, originId="doc1")

    c = KnwlChunk(content="Hello", tokens=0, index=0, originId="doc1")
    # id is assigned based on the content
    assert "chunk-" in c.id
    assert c.id == hash_with_prefix(c.content, prefix="chunk-")


def test_document_class():
    with pytest.raises(ValueError):
        KnwlDocument(content="")

    c = KnwlDocument(content="Hello")
    # id is assigned based on the content
    assert "doc-" in c.id
    assert c.id == hash_with_prefix(c.content, prefix="doc-")


def test_node_class():
    with pytest.raises(ValueError):
        KnwlNode(name="")

    c = KnwlNode(name="Hello")
    # id is assigned based on the content
    assert "node-" in c.id
    assert c.id == KnwlNode.hash_node(c)


def test_edge_class():
    with pytest.raises(ValueError):
        KnwlEdge(sourceId="", targetId="")

    c = KnwlEdge(sourceId="a", targetId="b")
    # id is assigned based on the content
    assert "edge-" in c.id
    assert c.id == KnwlEdge.hash_edge(c)


import asyncio
import json
import os
import tempfile
from hashlib import md5
from unittest.mock import patch, MagicMock

import pytest

pytestmark = pytest.mark.basic

from knwl.config import resolve_dict
from knwl.models import KnwlAnswer
from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlNode import KnwlNode
from knwl.utils import (
    _ensure_directories_exist,
    _resolve_reference_path,
    _resolve_special_prefixes,
    clean_str,
    pack_messages,
    split_string_by_multi_markers,
    hash_with_prefix,
)
from knwl.utils import hash_args, get_json_body, get_full_path, parse_llm_record
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


def test_chunk_class():
    with pytest.raises(ValueError):
        KnwlChunk(content="", tokens=2, index=0, origin_id="doc1")

    c = KnwlChunk(content="Hello", tokens=0, index=0, origin_id="doc1")
    # id is assigned based on the content
    assert "chunk|>" in c.id
    assert c.id == hash_with_prefix(c.content, prefix="chunk|>")


def test_document_class():
    with pytest.raises(ValueError):
        KnwlDocument(content="")

    c = KnwlDocument(content="Hello")
    # id is assigned based on the content
    assert "doc|>" in c.id
    assert c.id == KnwlDocument.hash_keys("Hello")


def test_node_class():
    with pytest.raises(ValueError):
        KnwlNode(name="")

    c = KnwlNode(name="Hello")
    # id is assigned based on the content
    assert "node|>" in c.id
    assert c.id == KnwlNode.hash_node(c)


def test_edge_class():
    with pytest.raises(ValueError):
        KnwlEdge(source_id="", target_id="")

    c = KnwlEdge(source_id="a", target_id="b")
    # id is assigned based on the content
    assert "edge|>" in c.id
    assert c.id == KnwlEdge.hash_edge(c)


def test_args_hash():
    a = KnwlAnswer(
        messages=[{"content": "Hello"}], llm_service="ollama", llm_model="qwen2.5:14b"
    )
    print(a.model_dump_json())


def test_get_full_path():
    p = get_full_path("knwl.llm")
    assert p.endswith("knwl.llm")
    assert ".knwl" in p

    p = get_full_path("a/llm", "$/tests")
    assert p.endswith("a/llm")
    assert "/tests" in p

    p = get_full_path("$/tests/abc")
    assert p.endswith("abc")
    assert "/tests" in p


def test_hash():
    assert (
        hash_with_prefix("hello", "pre|>")
        == "pre|>" + md5("hello".encode()).hexdigest()
    )
    assert hash_with_prefix("", "pre|>") == "pre|>" + md5("".encode()).hexdigest()
    assert (
        hash_with_prefix("hello", "hash|>")
        == "hash|>" + md5("hello".encode()).hexdigest()
    )
    assert hash_with_prefix("", "hash|>") == "hash|>" + md5("".encode()).hexdigest()

    assert hash_with_prefix(
        json.dumps({"a": 1, "b": 2, "c": {"x": 23, "y": 0.1}}), "json|>"
    ) == hash_with_prefix(
        json.dumps({"a": 1, "b": 2, "c": {"x": 23, "y": 0.1}}), "json|>"
    )
    assert hash_with_prefix(
        json.dumps({"a": 1, "b": 2, "c": {"x": 23, "y": 0.1}}), "json|>"
    ) != hash_with_prefix(
        json.dumps({"a": 2, "b": 2, "c": {"x": 23, "y": 0.1}}), "json|>"
    )


def test_split_string_by_multi_markers_edge_cases():
    assert split_string_by_multi_markers("", [","]) == [""]
    assert split_string_by_multi_markers("No markers here", [","]) == [
        "No markers here"
    ]
    assert split_string_by_multi_markers(",,,", [","]) == []
    assert split_string_by_multi_markers("Hello,,,World", [","]) == ["Hello", "World"]
    assert split_string_by_multi_markers("Hello!!!World???Test", ["!!!", "???"]) == [
        "Hello",
        "World",
        "Test",
    ]

    assert (
        split_string_by_multi_markers("a|b|c$c|d|e$<END>k|l|m$<END>", ["$", "<END>"])
    ) == ["a|b|c", "c|d|e", "k|l|m"]


def test_get_full_path_none_input():
    """Test that None input returns None"""
    result = get_full_path(None)
    assert result is None


def test_get_full_path_non_string_input():
    """Test that non-string input raises ValueError"""
    with pytest.raises(ValueError, match="File path must be a string"):
        get_full_path(123)


def test_get_full_path_basic_file():
    """Test basic file path resolution with default $/data reference"""
    result = get_full_path("test.txt")
    assert result is not None
    assert result.endswith("test.txt")
    assert ".knwl" in result


def test_get_full_path_data_prefix():
    """Test $/data prefix resolution"""
    result = get_full_path("$/data/test.txt")
    assert result is not None
    assert result.endswith("test.txt")
    assert "data" in result


def test_get_full_path_root_prefix():
    """Test $/root prefix resolution"""
    result = get_full_path("$/root/test.txt")
    assert result is not None
    assert result.endswith("test.txt")


def test_get_full_path_test_prefix():
    """Test $/tests prefix resolution"""
    result = get_full_path("$/tests/test.txt")
    assert result is not None
    assert result.endswith("test.txt")
    assert "tests" in result


def test_get_full_path_with_reference_path():
    """Test with explicit reference path"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = get_full_path("test.txt", temp_dir)
        assert result is not None
        assert result.startswith(temp_dir)
        assert result.endswith("test.txt")


def test_get_full_path_with_data_reference():
    """Test with $/data reference path"""
    result = get_full_path("test.txt", "$/data")
    assert result is not None
    assert result.endswith("test.txt")
    assert "data" in result


def test_get_full_path_with_root_reference():
    """Test with $/root reference path"""
    result = get_full_path("test.txt", "$/root")
    assert result is not None
    assert result.endswith("test.txt")


def test_get_full_path_with_test_reference():
    """Test with $/tests reference path"""
    result = get_full_path("test.txt", "$/tests")
    assert result is not None
    assert result.endswith("test.txt")
    assert "tests" in result


def test_get_full_path_non_absolute_reference():
    """Test that non-absolute reference path raises FileNotFoundError"""
    with pytest.raises(FileNotFoundError, match="Reference path must be absolute"):
        get_full_path("test.txt", "relative/path")


def test_get_full_path_invalid_reference_type():
    """Test that non-string reference path raises ValueError"""
    with pytest.raises(ValueError, match="Reference path must be a string"):
        get_full_path("test.txt", 123)


def test_get_full_path_create_dirs_false():
    """Test with create_dirs=False"""
    result = get_full_path("test.txt", create_dirs=False)
    assert result is not None
    assert result.endswith("test.txt")


def test_get_full_path_nested_path():
    """Test with nested directory structure"""
    result = get_full_path("$/tests/subdir/nested/test.txt")
    assert result is not None
    assert result.endswith("subdir/nested/test.txt")


def test_get_full_path_absolute_result():
    """Test that result is always absolute path"""
    result = get_full_path("test.txt")
    assert result is not None
    assert os.path.isabs(result)


def test_resolve_special_prefixes():
    """Test _resolve_special_prefixes helper function"""
    # Test $/tests prefix
    path, ref = _resolve_special_prefixes("$/tests/file.txt")
    assert path == "./file.txt"
    assert ref == "$/tests"

    # Test $/data prefix
    path, ref = _resolve_special_prefixes("$/data/file.txt")
    assert path == "./file.txt"
    assert ref == "$/data"

    # Test $/root prefix
    path, ref = _resolve_special_prefixes("$/root/file.txt")
    assert path == "./file.txt"
    assert ref == "$/root"

    # Test no prefix
    path, ref = _resolve_special_prefixes("file.txt")
    assert path == "file.txt"
    assert ref is None


def test_resolve_reference_path():
    """Test _resolve_reference_path helper function"""
    # Test $/data resolution
    result = _resolve_reference_path("$/data", create_dirs=False)
    assert result is not None
    assert "data" in result

    # Test $/root resolution
    result = _resolve_reference_path("$/root", create_dirs=False)
    assert result is not None

    # Test $/tests resolution
    result = _resolve_reference_path("$/tests", create_dirs=False)
    assert result is not None
    assert "tests" in result


def test_resolve_reference_path_absolute():
    """Test _resolve_reference_path with absolute path"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = _resolve_reference_path(temp_dir, create_dirs=False)
        assert result == temp_dir


def test_resolve_reference_path_non_absolute():
    """Test _resolve_reference_path with non-absolute path raises error"""
    with pytest.raises(FileNotFoundError, match="Reference path must be absolute"):
        _resolve_reference_path("relative/path", create_dirs=False)


def test_ensure_directories_exist_file():
    """Test _ensure_directories_exist for file path"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "subdir", "test.txt")
        _ensure_directories_exist(file_path)
        assert os.path.exists(os.path.dirname(file_path))


def test_ensure_directories_exist_directory():
    """Test _ensure_directories_exist for directory path"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = os.path.join(temp_dir, "new_directory")
        _ensure_directories_exist(dir_path)
        assert os.path.exists(dir_path)


def test_ensure_directories_exist_error():
    """Test _ensure_directories_exist with creation error"""
    with patch("os.makedirs") as mock_makedirs:
        mock_makedirs.side_effect = OSError("Permission denied")

        with pytest.raises(OSError, match="Failed to create directories"):
            _ensure_directories_exist("/some/path/test.txt")


def test_special_dirs():
    p = get_full_path("$/root/xyz")
    print(p)
    assert p.endswith("xyz") and "knwl" in p and p.startswith("/")
    if os.path.exists(p):
        os.rmdir(p)

    p = get_full_path("$/user/abc")
    print(p)
    assert p.endswith("abc") and ".knwl" in p and p.startswith(os.path.expanduser("~"))
    if os.path.exists(p):
        os.rmdir(p)

    p = get_full_path("$/data/xyz")
    print(p)
    assert p.endswith("xyz") and p.startswith("/")
    if os.path.exists(p):
        os.rmdir(p)

    p = get_full_path("$/tests/xyz")
    print(p)
    assert p.endswith("xyz") and p.startswith("/")
    if os.path.exists(p):
        os.rmdir(p)


def test_parse_llm_record():
    rec = "(component1, component2, component3)"
    result = parse_llm_record(rec, delimiter=",")
    assert result == ["component1", "component2", "component3"]

    rec = "No parentheses here"
    result = parse_llm_record(rec, delimiter=",")
    assert result is None

    rec = ""
    result = parse_llm_record(rec, delimiter=",")
    assert result is None

    rec = None
    result = parse_llm_record(rec, delimiter=",")
    assert result is None

    rec_missing_end_parentheses = "(entity<|>Catherine Thomson Hogarth<|>person<|>Catherine Thomson Hogarth was the daughter of George Hogarth and became Charles Dickens's wife after a one-year engagement."
    result = parse_llm_record(rec_missing_end_parentheses, delimiter="<|>")
    assert result == [
        "entity",
        "Catherine Thomson Hogarth",
        "person",
        "Catherine Thomson Hogarth was the daughter of George Hogarth and became Charles Dickens's wife after a one-year engagement.",
    ]

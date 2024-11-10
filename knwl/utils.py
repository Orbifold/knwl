import asyncio
import html
import json
import os
import random
import re
import string
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from hashlib import md5
from typing import Any, Union, Literal, List, TypeVar, Callable, Dict
from uuid import uuid4
from .logging import logger

CATEGORY_KEYWORD_EXTRACTION = "Keywords Extraction"
CATEGORY_NAIVE_QUERY = "Naive Query"


def unique_strings(ar: List[str] | List[List[str]]) -> List[str]:
    if isinstance(ar[0], list):
        ar = [item for sublist in ar for item in sublist]
        return list(set(ar))
    else:
        return list(set(ar))


@dataclass(frozen=True)
class KnwlNode:
    """
    A class representing a knowledge node.

    Attributes:
        name (str): The name of the knowledge node. Can be unique but in a refined model it should not. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.
        type (str): The type of the knowledge node.
        description (str): A description of the knowledge node.
        chunkIds (List[str]): The chunk identifiers associated with the knowledge node.
        typeName (str): The type name of the knowledge node, default is "KnwlNode".
        id (str): The unique identifier of the knowledge node, default is a new UUID.
    """
    name: str
    type: str = field(default="UNKNOWN")
    typeName: str = "KnwlNode"
    id: str = field(default=None)
    description: str = field(default="")
    chunkIds: List[str] = field(default_factory=list)

    @staticmethod
    def hash_node(n: 'KnwlNode') -> str:
        return hash_with_prefix(n.name + " " + n.type + " " + (n.description or ""), prefix="node-")

    def update_id(self):
        if self.name is not None and len(str.strip(self.name)) > 0:
            object.__setattr__(self, "id", KnwlNode.hash_node(self))
        else:
            object.__setattr__(self, "id", None)

    def __post_init__(self):
        if self.name is None or len(str.strip(self.name)) == 0:
            raise ValueError("Content of a KnwlNode cannot be None or empty.")
        self.update_id()


@dataclass(frozen=True)
class KnwlEdge:
    """
    Represents a knowledge edge in a graph.

    Attributes:
        sourceId (str): The ID of the source node.
        targetId (str): The ID of the target node.
        chunkIds (str): The ID of the chunk.
        weight (float): The weight of the edge.
        description (str): A description of the edge.
        keywords (List(str)): Keywords associated with the edge.
        typeName (str): The type name of the edge, default is "KnwlEdge".
        id (str): The unique identifier of the edge, default is a new UUID.
    """
    sourceId: str
    targetId: str
    typeName: str = "KnwlEdge"
    id: str = field(default=str(uuid4()))
    chunkIds: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    description: str = field(default=None)
    weight: float = field(default=1.0)

    @staticmethod
    def hash_edge(e: 'KnwlEdge') -> str:
        return hash_with_prefix(e.sourceId + " " + e.targetId + " " + (e.description or "") + str(e.weight), prefix="edge-")

    def update_id(self):
        #  note that using only source and target is not enough to ensure uniqueness
        object.__setattr__(self, "id", KnwlEdge.hash_edge(self))

    def __post_init__(self):
        if self.sourceId is None or len(str.strip(self.sourceId)) == 0:
            raise ValueError("Source Id of a KnwlEdge cannot be None or empty.")
        if self.targetId is None or len(str.strip(self.targetId)) == 0:
            raise ValueError("Target Id of a KnwlEdge cannot be None or empty.")
        self.update_id()

    @staticmethod
    def other_endpoint(edge: 'KnwlEdge', node_id: str) -> str:
        if edge.sourceId == node_id:
            return edge.targetId
        elif edge.targetId == node_id:
            return edge.sourceId
        else:
            raise ValueError(f"Node {node_id} is not an endpoint of edge {edge.id}")


@dataclass(frozen=True)
class KnwlGraph:
    """
    A class used to represent a Knowledge Graph.

    Attributes
    ----------
    nodes : List[KnwlNode]
        A list of KnwlNode objects.
    edges : List[KnwlEdge]
        A list of KnwlEdge objects.
    typeName : str
        A string representing the type name of the graph, default is "KnwlGraph".
    id : str
        A unique identifier for the graph, default is a new UUID4 string.
    """
    nodes: List[KnwlNode]
    edges: List[KnwlEdge]
    typeName: str = "KnwlGraph"
    id: str = field(default=str(uuid4()))

    def is_consistent(self) -> bool:
        """
        Check if the graph is consistent: all the edge endpoints are in the node list.
        """
        node_ids = self.get_node_ids()
        edge_ids = self.get_edge_ids()

        for edge in self.edges:
            if edge.sourceId not in node_ids or edge.targetId not in node_ids:
                return False
        return True

    def get_node_ids(self) -> List[str]:
        return [node.id for node in self.nodes]

    def get_edge_ids(self) -> List[str]:
        return [edge.id for edge in self.edges]

    def __post_init__(self):
        if not self.is_consistent():
            raise ValueError("The graph is not consistent.")


@dataclass(frozen=True)
class KnwlDocument:
    """
    A (immutable) class representing a source document.

    Attributes:
        content (str): The content of the source document.
        id (str): A unique identifier for the source document. Defaults to a new UUID.
        timestamp (str): The timestamp when the source document was created. Defaults to the current time in ISO format.
        typeName (str): The type name of the source document. Defaults to "KnwlDocument".
        name (str): The name of the source document. Defaults to an empty string.
        description (str): A description of the source document. Defaults to an empty string.
    """

    content: str
    id: str = field(default=None)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = field(default="")
    name: str = field(default="")
    typeName: str = "KnwlDocument"

    def update_id(self):
        if self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(self, "id", hash_with_prefix(self.content, prefix="doc-"))
        else:
            object.__setattr__(self, "id", None)

    def __post_init__(self):
        if self.content is None or len(str.strip(self.content)) == 0:
            raise ValueError("Content of a KnwlDocument cannot be None or empty.")
        self.update_id()


@dataclass(frozen=True)
class KnwlChunk:
    tokens: int
    content: str
    originId: str = field(default=None)
    index: int = field(default=0)
    typeName: str = "KnwlChunk"
    id: str = field(default=None)

    def update_id(self):
        if self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(self, "id", hash_with_prefix(self.content, prefix="chunk-"))
        else:
            object.__setattr__(self, "id", None)

    def __post_init__(self):
        if self.content is None or len(str.strip(self.content)) == 0:
            raise ValueError("Content of a KnwlChunk cannot be None or empty.")
        self.update_id()


@dataclass(frozen=True)
class KnwlExtraction:
    """
    A class used to represent a Knowledge Extraction.

    Attributes
    ----------
    nodes : dict[str, List[KnwlNode]]
        A dictionary where the keys are strings and the values are lists of KnwlNode objects.
    edges : dict[str, List[KnwlEdge]]
        A dictionary where the keys are strings and the values are lists of KnwlEdge objects.
        Note that the key is the tuple of endpoints sorted in ascending order.
        The KG is undirected and the key is used to ensure that the same edge is not added twice.
    typeName : str
        A string representing the type name of the extraction, default is "KnwlExtraction".
    id : str
        A unique identifier for the extraction, default is a new UUID4 string.
    """
    nodes: dict[str, List[KnwlNode]]
    edges: dict[str, List[KnwlEdge]]
    typeName: str = "KnwlExtraction"
    id: str = field(default=str(uuid4()))


class StorageNameSpace:
    namespace: str

    def __init__(self, namespace: str = "default"):
        self.namespace = namespace


@dataclass
class QueryParam:
    mode: Literal["local", "global", "hybrid", "naive"] = "global"

    only_need_context: bool = False

    response_type: str = "Multiple Paragraphs"

    # Number of top-k items to retrieve; corresponds to entities in "local" mode and relationships in "global" mode.
    top_k: int = 60

    # Number of tokens for the original chunks.
    max_token_for_text_unit: int = 4000

    # Number of tokens for the relationship descriptions
    max_token_for_global_context: int = 4000

    # Number of tokens for the entity descriptions
    max_token_for_local_context: int = 4000


@dataclass(frozen=True)
class KnwlDegreeNode(KnwlNode):
    """
    A class representing a knowledge node with a degree.

    Attributes:
        name (str): The name of the knowledge node. Can be unique but in a refined model it should not. For example, 'apple' can be both a noun and a company. The name+type should be unique instead.
        type (str): The type of the knowledge node.
        description (str): A description of the knowledge node.
        chunkIds (List[str]): The chunk identifiers associated with the knowledge node.
        degree (int): The degree of the node.
        typeName (str): The type name of the knowledge node, default is "KnwlNode".
        id (str): The unique identifier of the knowledge node, default is a new UUID.
    """
    degree: int = field(default=0)


def get_json_body(content: str) -> Union[str, None]:
    """
    Locate the first JSON string body in a string.
    """
    if content is None:
        raise ValueError("Content cannot be None")
    stack = []
    start = -1
    for i, char in enumerate(content):
        if char == "{":
            if start == -1:
                start = i
            stack.append(char)
        elif char == "}":
            if stack:
                stack.pop()
                if not stack:
                    return content[start: i + 1]
    if start != -1 and stack:
        return content[start:]
    else:
        return None


def random_name(length=8):
    """
    Generate a random name consisting of lowercase letters.

    Args:
        length (int): The length of the generated name. Default is 8.

    Returns:
        str: A randomly generated name of the specified length.
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def convert_response_to_json(response: str) -> dict:
    """
    If there is a JSON-like thing in the response, it gets extracted.

    Nothing magical here, simply trying to fetch it via a regex.

    Args:
        response (str): The response string containing the JSON data.

    Returns:
        dict: The parsed JSON data as a dictionary.

    Raises:
        AssertionError: If the JSON string cannot be located in the response.
        json.JSONDecodeError: If the JSON string cannot be parsed into a dictionary.
    """
    json_str = get_json_body(response)
    assert json_str is not None, f"Unable to parse JSON from response: {
    response}"
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {json_str}")
        raise e from None


def hash_args(*args):
    """
    Computes an MD5 hash for the given arguments.

    Args:
        *args: Variable length argument list.

    Returns:
        str: The MD5 hash of the arguments as a hexadecimal string.
    """
    return md5(str(args).encode()).hexdigest()


def hash_with_prefix(content, prefix: str = ""):
    """
    Computes an MD5 hash of the given content and returns it as a string with an optional prefix.

    Args:
        content (str): The content to hash.
        prefix (str, optional): A string to prepend to the hash. Defaults to an empty string.

    Returns:
        str: The MD5 hash of the content, optionally prefixed.
    """
    return prefix + md5(content.encode()).hexdigest()


def throttle(max_size: int, waitting_time: float = 0.0001):
    """
    A decorator to limit the number of concurrent asynchronous function calls.
    Args:
        max_size (int): The maximum number of concurrent calls allowed.
        waitting_time (float, optional): The time to wait before checking the limit again. Defaults to 0.0001 seconds.
    Returns:
        function: A decorator that limits the number of concurrent calls to the decorated async function.
    """

    def wrapper(func):
        __current_size = 0

        @wraps(func)
        async def wait_func(*args, **kwargs):
            nonlocal __current_size
            while __current_size >= max_size:
                await asyncio.sleep(waitting_time)
            __current_size += 1
            result = await func(*args, **kwargs)
            __current_size -= 1
            return result

        return wait_func

    return wrapper


def load_json(file_name):
    """
    Loads a JSON file and returns its contents as a Python object.

    Args:
        file_name (str): The path to the JSON file to be loaded.

    Returns:
        dict or list: The contents of the JSON file as a Python dictionary or list.
        None: If the file does not exist.
    """
    if not os.path.exists(file_name):
        return None
    with open(file_name, encoding="utf-8") as f:
        return json.load(f)


def write_json(json_obj, file_name):
    """
    Write a JSON object to a file.

    Args:
        json_obj (dict): The JSON object to write to the file.
        file_name (str): The name of the file to write the JSON object to.

    Returns:
        None
    """
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(json_obj, f, indent=2, ensure_ascii=False)


def pack_messages(*args: str):
    """
    Packs a variable number of string arguments into a list of dictionaries with alternating roles.

    Args:
        *args (str): Variable number of string arguments representing messages.

    Returns:
        list: A list of dictionaries, each containing a 'role' key with values alternating between 'user' and 'assistant',
              and a 'content' key with the corresponding message content.
    """
    roles = ["user", "assistant"]
    return [
        {"role": roles[i % 2], "content": content} for i, content in enumerate(args)
    ]


def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
    """
    Splits a string by multiple markers and returns a list of the resulting substrings.

    Args:
        content (str): The string to be split.
        markers (list[str]): A list of marker strings to split the content by.

    Returns:
        list[str]: A list of substrings obtained by splitting the content by the markers.
                   Leading and trailing whitespace is removed from each substring.
                   Empty substrings are excluded from the result.

    Examples:
        >>> split_string_by_multi_markers("hello,world;this is a test", [",", ";"])
        ['hello', 'world', 'this is a test']
    """
    if not markers:
        return [content]
    if content == "":
        return [""]
    results = re.split("|".join(re.escape(marker)
                                for marker in markers), content)
    return [r.strip().replace("\"", "") for r in results if r.strip()]


def clean_str(input: Any) -> str:
    """
    Cleans the input string by performing the following operations:
    1. If the input is not a string, it returns the input as is.
    2. Strips leading and trailing whitespace from the string.
    3. Unescapes any HTML entities in the string.
    4. Removes control characters from the string.
    Args:
        input (Any): The input to be cleaned. Expected to be a string.
    Returns:
        str: The cleaned string.
    """

    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())

    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)


def is_float_regex(value):
    return bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", value))


def list_of_list_to_csv(data: list[list]):
    return "\n".join(
        [",\t".join([str(data_dd) for data_dd in data_d]) for data_d in data]
    )


def save_data_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

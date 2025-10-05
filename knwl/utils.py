import asyncio
import html
import json
import os
import random
import re
import string
from functools import wraps
from hashlib import md5
from typing import Any, Union, List

from .logging import logger

CATEGORY_KEYWORD_EXTRACTION = "Keywords Extraction"
CATEGORY_NAIVE_QUERY = "Naive Query"
CATEGORY_GLEANING = "Gleaning"
CATEGORY_NEED_MORE = "Need more extraction"


def get_endpoint_ids(key: str) -> tuple[str | None, str | None]:
    found = re.search(r"\((.*)\)", key)
    if found is None:
        return None, None
    found = found.group(1)
    return found.split(",")[0], found.split(",")[1]


def unique_strings(ar: List[str] | List[List[str]]) -> List[str]:
    if ar is None:
        return []
    if len(ar) == 0:
        return []
    if isinstance(ar[0], list):
        ar = [item for sublist in ar for item in sublist]
        return list(set(ar))
    else:
        return list(set(ar))


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
    return "".join(random.choice(letters) for i in range(length))


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
    assert json_str is not None, f"Unable to parse JSON from response: {response}"
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
    return [{"role": roles[i % 2], "content": content} for i, content in enumerate(args)]


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
    results = re.split("|".join(re.escape(marker) for marker in markers), content)
    return [r.strip().replace('"', "") for r in results if r.strip()]


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
    return "\n".join([",\t".join([str(data_dd) for data_dd in data_d]) for data_d in data])


def save_data_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_info() -> dict:
    """
    Retrieves project information from the `pyproject.toml` file.
    """
    import toml

    current_dir = os.path.dirname(os.path.abspath(__file__))
    pyproject_path = os.path.join(current_dir, "..", "pyproject.toml")
    with open(pyproject_path, "r") as file:
        pyproject_data = toml.load(file)
    version = pyproject_data["project"]["version"]
    name = pyproject_data["project"]["name"]
    author = pyproject_data["project"]["authors"][0]
    description = pyproject_data["project"]["description"]
    return {"name": name, "version": version, "author": author, "description": description, }


def merge_dictionaries(source: dict, destination: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge_dictionaries(value, node)
        else:
            destination[key] = value
    return destination


def get_full_path(file_path: str, reference_path: str = None) -> str | None:
    if file_path is None:
        return None
    if file_path.startswith("$test"):
        return get_full_path("." + file_path[5:], "$test")
    if file_path.startswith("$data"):
        return get_full_path("." + file_path[6:], "$data")

    if reference_path == "$data":
        current_dir = os.path.dirname(os.path.abspath(__file__))
        reference_path = os.path.join(current_dir, "..", "data")
    if reference_path == "$test":
        current_dir = os.path.dirname(os.path.abspath(__file__))
        reference_path = os.path.join(current_dir, "..", "tests", "data")
    if reference_path is not None:
        if not os.path.isabs(reference_path):
            raise FileNotFoundError(reference_path)
        # ensure the reference path is a string
        if not isinstance(reference_path, str):
            raise ValueError("Reference path must be a string")
        if not os.path.exists(reference_path):
            os.makedirs(reference_path, exist_ok=True)

    if file_path is None:
        raise ValueError("File path cannot be None")
    if not isinstance(file_path, str):
        raise ValueError("File path must be a string")

    if reference_path is None:
        return get_full_path(file_path, "$data")

    p = os.path.join(reference_path, file_path)
    if not p.endswith('/') and not p.endswith('\\') and '.' in os.path.basename(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
    else:
        os.makedirs(p, exist_ok=True)
    return p

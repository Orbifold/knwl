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
from datetime import datetime


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


def unique_strings(ar: list[str] | list[list[str]]) -> list[str]:
    if ar is None:
        return []
    if len(ar) == 0:
        return []
    if isinstance(ar[0], list):
        ar = [item for sublist in ar for item in sublist if item is not None]
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
                    return content[start : i + 1]
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


def hash_args(*args):
    """
    Computes an MD5 hash for the given arguments.

    Args:
        *args: Variable length argument list.

    Returns:
        str: The MD5 hash of the arguments as a hexadecimal string.
    """
    return md5(str(args).encode()).hexdigest()


def hash_with_prefix(content: Any, prefix: str = ""):
    """
    Computes an MD5 hash of the given content and returns it as a string with an optional prefix.

    Args:
        content (str): The content to hash.
        prefix (str, optional): A string to prepend to the hash. Defaults to an empty string.

    Returns:
        str: The MD5 hash of the content, optionally prefixed.
    """
    if isinstance(content, dict):
        content = json.dumps(content, sort_keys=True)
    elif hasattr(content, "model_dump_json"):
        content = content.model_dump_json()
    else:
        content = str(content)
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
    return "\n".join(
        [",\t".join([str(data_dd) for data_dd in data_d]) for data_d in data]
    )


def save_data_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_project_info() -> dict:
    """
    Retrieves project information from the `pyproject.toml` file.
    Important: the toml file is not available after packaging (PyPI), so this function
    should only be used during development.
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
    return {
        "name": name,
        "version": version,
        "author": author,
        "description": description,
    }


def merge_dictionaries(source: dict, destination: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge_dictionaries(value, node)
        else:
            destination[key] = value
    return destination


def get_full_path(
    file_path: str, reference_path: str = None, create_dirs: bool = True
) -> str | None:
    """
    Resolves a file path to its full absolute path, supporting special path prefixes.

    Special prefixes:
    - $/data: Resolves to the project's data directory
    - $/root: Resolves to the project root directory
    - $/tests: Resolves to the test data directory
    - "$/user": Resolves to the user's Knwl directory (e.g., ~/.knwl)

    Args:
        file_path (str): The file path to resolve. Can use special prefixes.
        reference_path (str, optional): Base directory or special prefix to resolve relative to.
        create_dirs (bool): Whether to create directories if they don't exist.

    Returns:
        str | None: The resolved absolute path, or None if file_path is None.

    Raises:
        ValueError: If file_path is not a string or reference_path format is invalid.
        FileNotFoundError: If reference_path is not absolute when required.
        OSError: If directory creation fails.
    """
    if file_path is None:
        return None

    if not isinstance(file_path, str):
        raise ValueError("File path must be a string")

    # Handle special "test" shorthand
    if file_path.lower() == "test":
        timestamp = round(datetime.now().timestamp())
        return get_full_path(f"test_{timestamp}.json", "$/tests", create_dirs)

    # Process special prefixes
    file_path, resolved_reference = _resolve_special_prefixes(file_path)
    if resolved_reference:
        reference_path = resolved_reference

    # Resolve reference path to absolute directory
    if reference_path is not None:
        reference_path = _resolve_reference_path(reference_path, create_dirs)
    else:
        # Default to $/user directory
        reference_path = _resolve_reference_path("$/user", create_dirs)

    # Construct final path
    full_path = os.path.join(reference_path, file_path)

    # Create directories if needed
    if create_dirs:
        _ensure_directories_exist(full_path)

    return os.path.abspath(full_path)


def _resolve_special_prefixes(file_path: str) -> tuple[str, str | None]:
    """Resolve special prefixes in file path and return cleaned path and reference."""
    prefix_map = {
        "$/tests": ("$/tests", 7),
        "$/data": ("$/data", 6),
        "$/root": ("$/root", 6),
        "$/user": ("$/user", 6),
    }

    for prefix, (ref_path, prefix_len) in prefix_map.items():
        if file_path.startswith(prefix):
            rest = file_path[prefix_len:]
            if rest.startswith("/"):
                rest = "." + rest
            return rest, ref_path

    return file_path, None


def _resolve_reference_path(reference_path: str, create_dirs: bool) -> str:
    """Resolve reference path to absolute directory path."""
    if not isinstance(reference_path, str):
        raise ValueError("Reference path must be a string")

    current_dir = os.path.dirname(os.path.abspath(__file__))

    special_paths = {
        "$/data": os.path.join(current_dir, "..", "data"),
        "$/root": os.path.join(current_dir, ".."),
        "$/user": os.path.join(os.path.expanduser("~"), ".knwl"),
        "$/tests": os.path.join(current_dir, "..", "tests", "data"),
    }

    if reference_path in special_paths:
        resolved_path = os.path.abspath(special_paths[reference_path])
    else:
        if not os.path.isabs(reference_path):
            raise FileNotFoundError(
                f"Reference path must be absolute: {reference_path}"
            )
        resolved_path = reference_path

    if create_dirs and not os.path.exists(resolved_path):
        try:
            os.makedirs(resolved_path, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create directory {resolved_path}: {e}")

    return resolved_path


def _ensure_directories_exist(full_path: str) -> None:
    """Ensure parent directories exist for the given path."""
    try:
        # Check if path appears to be a file (has extension) or directory
        if "." in os.path.basename(full_path) and not full_path.endswith(("/", "\\")):
            # It's a file, create parent directory
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
        else:
            # It's a directory, create it
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create directories for {full_path}: {e}")


def parse_llm_record(rec: str, delimiter: str = "|") -> list[str] | None:
    """
    Parses a record string formatted with custom delimiters and returns a list of its components.

    The expected format of the record string is:
    ("type"<|>"entity1"<|>"entity2"<|>"context"<|>"tags"<|>score)

    Args:
        rec (str): The record string to be parsed.

    Returns:
        list[str]|None: A list containing the components of the record if parsing is successful,
                        otherwise None if the format is incorrect.
    """
    is_a_record = lambda text: re.match(r"^\(.*\)$", text) is not None
    if rec is None or rec.strip() == "":
        return None
    
    if is_a_record(rec) is False:
        # second attempt with ending parenthesis added
        rec = rec + ")"
        if is_a_record(rec) is False:
            # giving up
            from knwl.logging import log

            log.error(f"Given text is likely not an LLM record: {rec}")
            return None
        
    record = re.search(r"^\((.*)\)$", rec.strip())    
    record = record.group(1)
    parts = split_string_by_multi_markers(record, [delimiter])

    return parts


def is_entity(record: list[str]):
    """
    Check if the given record represents an entity.

    Args:
        record (list[str]): A list of strings representing a record.

    Returns:
        bool: True if the record is an entity, False otherwise.
    """
    if record is None:
        return False
    return len(record) >= 4 and record[0] == "entity"


def is_relationship(record: list[str]):
    """
    Determines if the given record attributes represent a relationship.

    Args:
        record_attributes (list[str]): A list of strings representing the attributes of a record.

    Returns:
        bool: True if the record attributes represent a relationship, False otherwise.
    """
    if record is None:
        return False
    return len(record) >= 5 and record[0] == "relationship"


def answer_to_records(answer: str) -> list[list] | None:
    from knwl.prompts import prompts

    if not answer or answer.strip() == "":
        return None
    parts = split_string_by_multi_markers(
        answer,
        [
            prompts.constants.DEFAULT_RECORD_DELIMITER,
            prompts.constants.DEFAULT_COMPLETION_DELIMITER,
        ],
    )
    coll = []
    for part in parts:
        rec = parse_llm_record(part, prompts.constants.DEFAULT_TUPLE_DELIMITER)

        if rec:
            coll.append(rec)
    return coll

from collections import defaultdict
from typing import Dict

from knwl.prompts import prompts

from .models.KnwlChunk import KnwlChunk
from .models.KnwlEdge import KnwlEdge
from .models.KnwlExtraction import KnwlExtraction
from .models.KnwlNode import KnwlNode
from .utils import *

GRAPH_FIELD_SEP = prompts.constants.GRAPH_FIELD_SEP
DEFAULT_TUPLE_DELIMITER = prompts.constants.DEFAULT_TUPLE_DELIMITER
DEFAULT_RECORD_DELIMITER = prompts.constants.DEFAULT_RECORD_DELIMITER
DEFAULT_COMPLETION_DELIMITER = prompts.constants.DEFAULT_COMPLETION_DELIMITER
DEFAULT_ENTITY_TYPES = prompts.constants.DEFAULT_ENTITY_TYPES
ENTITY_EXTRACTION_PROMPT = prompts.extraction.full_entity_extraction

async def extract_entities(chunks: Dict[str, KnwlChunk]) -> KnwlExtraction | None:
    """
    Extracts entities from the given chunks and returns them as nodes and edges.

    Args:
        chunks (Dict[str, KnwlChunk]): A dictionary where keys are chunk identifiers and values are Chunk objects.

    Returns:
        Tuple[Dict[str, List], Dict[Tuple[str, str], List]]:
            - A dictionary of nodes where keys are entity types and values are lists of entities.
            - A dictionary of edges where keys are tuples of sorted entity types and values are lists of relationships.

    Notes:
        - The function uses asyncio.gather to process chunks concurrently.
        - The nodes and edges are returned as regular dictionaries for JSON serialization compatibility.
        - The keys of the edges dictionary are tuples, which are not directly JSON serializable.
    """
    chunk_list = list(chunks.items())
    if len(chunk_list) == 0:
        return None

    # use_llm_func is wrapped in ascynio.Semaphore, limiting max_async callings
    results: List[KnwlExtraction] = await asyncio.gather(
        *[process_chunk(k, v) for k, v in chunk_list]
    )
    if results is None:
        return None
    nodes = defaultdict(list)
    edges = defaultdict(list)
    for ex in results:
        if ex is None:
            continue
        if ex.nodes is None:
            continue
        for k, v in ex.nodes.items():
            nodes[k].extend(v)
        if ex.edges is None:
            continue
        for k, v in ex.edges.items():
            edges[k].extend(v)
    # the defaultdict is not very friendly to json serialization
    # event with this, the key of a relationship is a tuple, which is not json serializable
    g = KnwlExtraction(
        nodes={k: v for k, v in nodes.items()}, edges={k: v for k, v in edges.items()}
    )
    if len(g.nodes) == 0 and len(g.edges) == 0:
        return None
    return g


def stringify_keys(d):
    if isinstance(d, dict):
        return {str(k): stringify_keys(v) for k, v in d.items()}
    if isinstance(d, (list, tuple)):
        return type(d)(stringify_keys(v) for v in d)
    return d


async def extract_entities_as_json(chunks: Dict[str, KnwlChunk]):
    nodes, edges = await extract_entities(chunks)

    return stringify_keys({"entities": nodes, "relationships": edges})


async def process_chunk(chunk_key: str, chunk: KnwlChunk) -> KnwlExtraction | None:
    """
    Process a chunk of text to extract entities and relationships.

    Args:
        chunk_key (str): The key identifying the chunk.
        chunk (KnwlChunk): The chunk object containing content and tokens.

    Returns:
        Tuple[dict, dict]: A tuple containing two dictionaries:
            - nodes: A dictionary where keys are entity names and values are lists of entity attributes.
            - edges: A dictionary where keys are tuples of (src_id, tgt_id) and values are lists of relationship attributes.

    The function performs the following steps:
        1. Checks if the chunk content is empty or contains only whitespace, or if the token count is zero.
        2. Constructs prompts for entity extraction and continuation.
        3. Uses the `llm.ask` function to generate responses based on the prompts.
        4. Iteratively gleans additional information until a maximum number of iterations is reached or a stopping condition is met.
        5. Splits the final result into records and processes each record to identify entities and relationships.
        6. Converts records to entities or relationships and adds them to the respective dictionaries.
    """
    if not chunk.content:
        return None
    if chunk.content.strip() == "":
        return None
    if chunk.tokens == 0:
        return None

    content = chunk.content
    g: KnwlExtraction = await extract_graph_elements_from_text(content, chunk_key)
    return g


async def fast_entity_extraction_from_text(text: str) -> list[KnwlNode]:
    """
    Extract entities from the given text without gleaning or relationships.
    It does try to merge multiple entities with the same name.
    Mostly for experimentation and CLI, it is not used in the actual graph RAG flow.
    """
    context_base = dict(
        tuple_delimiter=DEFAULT_TUPLE_DELIMITER,
        record_delimiter=DEFAULT_RECORD_DELIMITER,
        completion_delimiter=DEFAULT_COMPLETION_DELIMITER,
        entity_types=",".join(DEFAULT_ENTITY_TYPES),
    )
    final_prompt = ENTITY_EXTRACTION_PROMPT.format(**context_base, input_text=text)
    # print(final_prompt)
    final_answer = await llm.ask(
        final_prompt, core_input=text, category=CATEGORY_KEYWORD_EXTRACTION
    )
    final_result = final_answer.answer
    records = split_string_by_multi_markers(
        final_result,
        [context_base["record_delimiter"], context_base["completion_delimiter"]],
    )
    nodes = []
    for record in records:
        record = re.search(r"\((.*)\)", record)
        if record is None:
            continue
        record = record.group(1)
        record_attributes = split_string_by_multi_markers(
            record, [context_base["tuple_delimiter"]]
        )
        node: KnwlNode = KnwlNode(
            name=record_attributes[0],
            type=record_attributes[1].replace('<','').replace('>',''),
            description=record_attributes[2],
            chunkIds=[],
        )
        nodes.append(node)
    # print([node.name for node in nodes])
    return nodes


async def extract_graph_elements_from_text(
        text: str, chunk_key: str = None
) -> KnwlExtraction:
    """

    This extract the entities and relationships from the given tet.
    The returned extraction is a graph with semantic id's. That is, the name of the entities are unique within this graphs and can be used as such.
    Once merged into the larger knowledge graph they are not unique anymore and the id's are converted to the proper KnwlNode and KnwlEdge id's.

    Args:
        text:
        chunk_key:

    Returns:

    """
    
    continue_prompt = prompts.extraction.iterate_entity_extraction
    if_loop_prompt = prompts.extraction.glean_break

    context_base = dict(
        tuple_delimiter=DEFAULT_TUPLE_DELIMITER,
        record_delimiter=DEFAULT_RECORD_DELIMITER,
        completion_delimiter=DEFAULT_COMPLETION_DELIMITER,
        entity_types=",".join(DEFAULT_ENTITY_TYPES),
    )
    final_prompt = ENTITY_EXTRACTION_PROMPT.format(**context_base, input_text=text)
    final_answer = await llm.ask(
        final_prompt, core_input=text, category=CATEGORY_KEYWORD_EXTRACTION
    )
    final_result = final_answer.answer
    history = pack_messages(final_prompt, final_result)
    entity_extract_max_gleaning = config.entity_extract_max_gleaning
    for now_glean_index in range(entity_extract_max_gleaning):
        glean_answer = await llm.ask(
            continue_prompt, history_messages=history, category=CATEGORY_GLEANING
        )
        glean_result = glean_answer.answer

        history += pack_messages(continue_prompt, glean_result)
        final_result += glean_result
        if now_glean_index == entity_extract_max_gleaning - 1:
            break

        if_loop_answer = await llm.ask(
            if_loop_prompt, history_messages=history, category=CATEGORY_NEED_MORE
        )
        if_loop_result = if_loop_answer.answer
        if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
        if if_loop_result != "yes":
            break

    records = split_string_by_multi_markers(
        final_result,
        [context_base["record_delimiter"], context_base["completion_delimiter"]],
    )

    nodes: dict[str, List[KnwlNode]] = {}
    edges: dict[str, List[KnwlEdge]] = {}
    node_map = {}  # map of node names to node ids
    for record in records:
        record = re.search(r"\((.*)\)", record)
        if record is None:
            continue
        record = record.group(1)
        record_attributes = split_string_by_multi_markers(
            record, [context_base["tuple_delimiter"]]
        )

        if is_entity(record_attributes):
            node: KnwlNode = await convert_record_to_node(record_attributes, chunk_key)
            if node.name not in nodes:
                nodes[node.name] = [node]
            else:
                coll = nodes[node.name]
                found = [
                    e
                    for e in coll
                    if e.type == node.type and e.description == node.description
                ]
                if len(found) == 0:
                    coll.append(node)
            node_map[node.name] = node.id
        elif is_relationship(record_attributes):
            edge: KnwlEdge = await convert_record_to_edge(record_attributes, chunk_key)
            # the edge key is the tuple of the source and target names, NOT the ids. Is corrected below
            edge_key = f"({edge.sourceId},{edge.targetId})"
            if (edge.sourceId, edge.targetId) not in edges:
                edges[edge_key] = [edge]
            else:
                coll = edges[edge_key]
                found = [
                    e
                    for e in coll
                    if e.description == edge.description and e.keywords == edge.keywords
                ]
                if len(found) == 0:
                    coll.append(edge)
    # the edge endpoints are the names and not the ids
    corrected_edges = {}
    for key in edges:
        for e in edges[key]:

            if e.sourceId not in node_map or e.targetId not in node_map:
                #  happens if the LLM creates edges to entities that are not in the graph
                continue
            if key not in corrected_edges:
                corrected_edges[key] = []
            source_id = node_map[e.sourceId]
            target_id = node_map[e.targetId]
            corrected_edge = KnwlEdge(
                sourceId=source_id,
                targetId=target_id,
                description=e.description,
                keywords=e.keywords,
                weight=e.weight,
                chunkIds=e.chunkIds,
            )
            corrected_edges[key].append(corrected_edge)
    return KnwlExtraction(nodes=nodes, edges=corrected_edges)


async def extract_graph_from_text(text: str) -> dict:
    """
    Extracts a JSON entity-relation graph from the given text.
    """
    nodes, edges = await extract_graph_elements_from_text(text)

    G = {"nodes": [], "edges": []}
    for node in nodes:
        G["nodes"].append(
            {
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "description": node.description,
                "chunkIds": node.chunkIds,
            }
        )
    for edge in edges:
        G["edges"].append(
            {
                "source": edge.sourceId,
                "target": edge.targetId,
                "description": edge.description,
                "keywords": edge.keywords,
                "weight": edge.weight,
                "chunkIds": edge.chunkIds,
            }
        )
    return G


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


async def convert_record_to_node(
        record: list[str], chunk_key: str = None
) -> KnwlNode | None:
    """
    Extracts and cleans entity information from a list of record attributes.
    Args:
        record (list[str]): A list of strings containing entity attributes.
        chunk_key (str): A string representing the source identifier for the entity.
    Returns:
        dict or None: A dictionary containing cleaned entity information with keys
        'entity_name', 'entity_type', 'description', and 'source_id'. Returns None
        if the entity name is empty after cleaning.
    """

    entity_name = clean_str(record[1].upper())
    if not entity_name.strip():
        return None
    entity_type = clean_str(record[2].upper())
    entity_description = clean_str(record[3])
    return KnwlNode(
        name=entity_name,
        type=entity_type,
        description=entity_description,
        chunkIds=[chunk_key] if chunk_key else [],
    )


async def convert_record_to_edge(
        record: list[str],
        chunk_key: str,
) -> KnwlEdge:
    """
    Converts a record to a KnwlRelationship object.
    Args:
        record (list[str]): A list of strings representing the record. The list is expected to have the following elements:
            - record[1]: Source node identifier (will be converted to uppercase and cleaned).
            - record[2]: Target node identifier (will be converted to uppercase and cleaned).
            - record[3]: Edge description (will be cleaned).
            - record[4]: Edge keywords (will be cleaned).
            - record[-1]: Weight of the edge (if it can be converted to float, otherwise defaults to 1.0).
        chunk_key (str): Identifier for the chunk from which the record originates.
    Returns:
        KnwlEdge: An instance of KnwlRelationship with the processed data.
    """

    # add this record as an edge in the G
    source = clean_str(record[1].upper())
    target = clean_str(record[2].upper())
    # the graph is undirected but we sort the nodes to make sure the edge is unique
    if source > target:
        source, target = target, source
    edge_description = clean_str(record[3])

    edge_keywords = [clean_str(u) for u in clean_str(record[4]).split(",")]
    edge_chunk_id = chunk_key
    weight = float(record[-1]) if is_float_regex(record[-1]) else 1.0
    return KnwlEdge(
        sourceId=source,
        targetId=target,
        description=edge_description,
        keywords=edge_keywords,
        weight=weight,
        chunkIds=[edge_chunk_id],
    )

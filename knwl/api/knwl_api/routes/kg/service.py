"""
Knowledge Graph Service Layer

This module provides business logic for knowledge graph operations,
including background job processing, CRUD operations, and RAG queries.

Architecture:
    - Background jobs are processed via TaskIQ for async operations
    - CRUD operations are synchronous proxies to the Knwl instance
    - RAG queries support multiple strategies (local, global, hybrid, naive, self)

Thread Safety:
    - The knwl instance is shared across requests
    - All operations are async-safe
"""

import logging
import time
from enum import Enum
from typing import Optional

from knwl import Knwl, KnwlInput, KnwlParams, KnwlAnswer, KnwlContext
from knwl.api.knwl_api.models.JobStatus import JobStatus, JobState
from knwl.api.knwl_api.taskiq_broker import broker
from knwl.models import KnwlDocument, KnwlNode
from knwl.models.KnwlFact import KnwlFact

# Configure logger
logger = logging.getLogger(__name__)


class JobType(str, Enum):
    """Enumeration of supported background job types."""

    INGEST = "ingest"
    EXTRACT = "extract"
    FACT = "fact"


# Initialize Knwl instance with default namespace
# This is a singleton shared across all requests
knwl = Knwl()


@broker.task
async def process_ingest_job(doc_data: dict) -> dict:
    """
    Background task to process data ingestion.

    Chunks the document, extracts entities/relationships, and stores them
    in the graph database and vector store.

    Args:
        doc_data: Dictionary representation of KnwlDocument

    Returns:
        Dict containing ingestion results and timing information

    Raises:
        Exception: Any error during ingestion (captured by TaskIQ)
    """
    started_at = time.time()

    try:
        logger.info(
            f"Starting ingestion job for document: {doc_data.get('name', 'unnamed')}"
        )
        doc = KnwlDocument(**doc_data)
        result = await knwl.ingest(doc)

        finished_at = time.time()
        duration = finished_at - started_at

        logger.info(f"Ingestion completed in {duration:.2f}s for: {doc.name}")

        result_dict = result.model_dump(mode="json")
        result_dict["started_at"] = started_at
        result_dict["finished_at"] = finished_at
        result_dict["duration"] = duration
        result_dict["job_type"] = JobType.INGEST.value

        return result_dict

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        logger.error(f"Ingestion failed after {duration:.2f}s: {str(e)}", exc_info=True)
        raise


@broker.task
async def process_extract_job(doc_data: dict) -> dict:
    """
    Background task to process data extraction.

    Extracts entities and relationships from a document without storing them.

    Args:
        doc_data: Dictionary representation of KnwlDocument

    Returns:
        Dict containing extraction results and timing information

    Raises:
        Exception: Any error during extraction (captured by TaskIQ)
    """
    started_at = time.time()

    try:
        logger.info(
            f"Starting extraction job for document: {doc_data.get('name', 'unnamed')}"
        )
        doc = KnwlDocument(**doc_data)
        result = await knwl.extract(doc)

        finished_at = time.time()
        duration = finished_at - started_at

        logger.info(f"Extraction completed in {duration:.2f}s for: {doc.name}")

        result_dict = result.model_dump(mode="json")
        result_dict["started_at"] = started_at
        result_dict["finished_at"] = finished_at
        result_dict["duration"] = duration
        result_dict["job_type"] = JobType.EXTRACT.value

        return result_dict

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        logger.error(
            f"Extraction failed after {duration:.2f}s: {str(e)}", exc_info=True
        )
        raise


@broker.task
async def process_fact_job(fact_data: dict) -> dict:
    """
    Background task to process adding a fact.

    Adds a single fact to the knowledge graph by extracting
    entities and relationships from the fact content.

    Args:
        fact_data: Dictionary representation of KnwlFact

    Returns:
        Dict containing fact addition results and timing information

    Raises:
        Exception: Any error during fact addition (captured by TaskIQ)
    """
    started_at = time.time()

    try:
        logger.info(
            f"Starting fact addition job for: {fact_data.get('name', 'unnamed')}"
        )
        fact = KnwlFact(**fact_data)
        result = await knwl.add_fact(
            name=fact.name, content=fact.content, type=fact.type, id=fact.id
        )

        finished_at = time.time()
        duration = finished_at - started_at

        logger.info(f"Fact addition completed in {duration:.2f}s for: {fact.name}")

        result_dict = result.model_dump(mode="json")
        result_dict["started_at"] = started_at
        result_dict["finished_at"] = finished_at
        result_dict["duration"] = duration
        result_dict["job_type"] = JobType.FACT.value

        return result_dict

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        logger.error(
            f"Fact addition failed after {duration:.2f}s: {str(e)}", exc_info=True
        )
        raise


async def add_job(job_type: str, data: dict) -> str:
    """
    Add a new job to the TaskIQ queue.

    This function validates the job type and dispatches the appropriate
    background task for processing.

    Args:
        job_type: Type of job to create ("ingest", "fact", or "extract")
        data: Job data (KnwlDocument or KnwlFact as dict)

    Returns:
        str: The unique job ID for tracking

    Raises:
        ValueError: If job_type is not recognized

    Example:
        >>> job_id = await add_job("ingest", {"text": "...", "name": "doc1"})
        >>> # Use job_id to check status later
    """
    logger.debug(f"Creating {job_type} job")

    # Dispatch to appropriate task handler
    if job_type == JobType.INGEST.value:
        task = await process_ingest_job.kiq(data)
    elif job_type == JobType.FACT.value:
        task = await process_fact_job.kiq(data)
    elif job_type == JobType.EXTRACT.value:
        task = await process_extract_job.kiq(data)
    else:
        valid_types = [jt.value for jt in JobType]
        raise ValueError(
            f"Unknown job type: '{job_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )

    logger.info(f"Job created with ID: {task.task_id} (type: {job_type})")
    return task.task_id


async def get_job_status(job_id: str) -> Optional[JobStatus]:
    """
    Retrieve the status of a given job.

    This function queries the TaskIQ result backend to get the current
    state of a background job.

    Args:
        job_id: The unique identifier of the job

    Returns:
        JobStatus if found, None if job doesn't exist or backend unavailable

    Job States:
        - RUNNING: Job is currently executing or pending
        - COMPLETED: Job finished successfully with results
        - FAILED: Job encountered an error during execution

    Example:
        >>> status = await get_job_status("abc-123")
        >>> if status and status.state == JobState.COMPLETED:
        >>>     print(f"Job completed in {status.finished_at - status.started_at}s")
    """
    # Check if result backend is configured
    if broker.result_backend is None:
        logger.warning("Result backend not configured - cannot retrieve job status")
        return None

    try:
        result = await broker.result_backend.get_result(job_id)
    except Exception as e:
        logger.error(f"Error retrieving job status for {job_id}: {str(e)}")
        return None

    if result is None:
        logger.debug(f"Job not found: {job_id}")
        return None

    # Map TaskIQ result state to our JobState
    if result.is_err:
        # Job failed with an error
        state = JobState.FAILED
        error = str(result.error) if result.error else "Unknown error"
        job_result = None
        started_at = 0
        finished_at = 0
        job_type = "Unknown"

        logger.warning(f"Job {job_id} failed: {error}")

    elif result.return_value is not None:
        # Job completed successfully
        state = JobState.COMPLETED
        error = None
        job_result = result.return_value
        started_at = job_result.get("started_at", 0)
        finished_at = job_result.get("finished_at", 0)
        job_type = job_result.get("job_type", "Unknown")
        duration = job_result.get(
            "duration", finished_at - started_at if finished_at else 0
        )

        logger.debug(f"Job {job_id} completed in {duration:.2f}s")

    else:
        # Task exists but no result yet - it's either pending or running
        state = JobState.RUNNING
        error = None
        job_result = None
        started_at = 0
        finished_at = 0
        job_type = "Unknown"

        logger.debug(f"Job {job_id} is still running")

    return JobStatus(
        job_id=job_id,
        state=state,
        result=job_result,
        error=error,
        started_at=started_at,
        finished_at=finished_at,
        job_type=job_type,
    )


# === Graph Statistics Operations ===


async def node_count() -> int:
    """
    Get the total number of nodes in the knowledge graph.

    Returns:
        int: The count of nodes in the current namespace

    Example:
        >>> count = await node_count()
        >>> print(f"Knowledge graph contains {count} entities")
    """
    try:
        count = await knwl.node_count()
        logger.debug(f"Node count retrieved: {count}")
        return count
    except Exception as e:
        logger.error(f"Failed to get node count: {str(e)}", exc_info=True)
        raise


async def edge_count() -> int:
    """
    Get the total number of edges in the knowledge graph.

    Returns:
        int: The count of edges (relationships) in the current namespace

    Example:
        >>> count = await edge_count()
        >>> print(f"Knowledge graph contains {count} relationships")
    """
    try:
        count = await knwl.edge_count()
        logger.debug(f"Edge count retrieved: {count}")
        return count
    except Exception as e:
        logger.error(f"Failed to get edge count: {str(e)}", exc_info=True)
        raise


async def get_namespace() -> str:
    """
    Get the current namespace of the knowledge graph.

    Namespaces allow logical separation of different knowledge graphs
    within the same storage backend.

    Returns:
        str: The namespace identifier

    Example:
        >>> ns = await get_namespace()
        >>> print(f"Current namespace: {ns}")
    """
    return knwl.namespace


# === Node CRUD Operations ===


async def get_node_by_id(id: str) -> Optional[KnwlNode]:
    """
    Retrieve a node by its unique identifier.

    Args:
        id: The unique identifier of the node

    Returns:
        KnwlNode if found, None otherwise

    Example:
        >>> node = await get_node_by_id("entity-123")
        >>> if node:
        >>>     print(f"Found: {node.name} ({node.type})")
    """
    try:
        logger.debug(f"Retrieving node: {id}")
        node = await knwl.get_node_by_id(id)

        if node:
            logger.debug(f"Node found: {node.name} (type: {node.type})")
        else:
            logger.debug(f"Node not found: {id}")

        return node

    except Exception as e:
        logger.error(f"Error retrieving node {id}: {str(e)}", exc_info=True)
        raise


async def delete_node_by_id(id: str) -> Optional[bool]:
    """
    Delete a node by its unique identifier.

    This operation removes the node and all its associated edges from
    the knowledge graph.

    Args:
        id: The unique identifier of the node to delete

    Returns:
        bool indicating success, or None if node not found

    Example:
        >>> success = await delete_node_by_id("entity-123")
        >>> if success:
        >>>     print("Node deleted successfully")
    """
    try:
        logger.info(f"Deleting node: {id}")
        result = await knwl.delete_node_by_id(id)

        if result:
            logger.info(f"Node deleted successfully: {id}")
        else:
            logger.warning(f"Node not found for deletion: {id}")

        return result

    except Exception as e:
        logger.error(f"Error deleting node {id}: {str(e)}", exc_info=True)
        raise


# === Graph RAG Query Operations ===


async def ask_question(question: str, strategy: Optional[str] = None) -> KnwlAnswer:
    """
    Ask a question to the knowledge graph and generate an answer.

    This function performs a complete RAG pipeline:
    1. Retrieves relevant context using the specified Graph RAG strategy
    2. Generates an LLM-based answer using the retrieved context

    Args:
        question: The question to ask (required, non-empty)
        strategy: Graph RAG strategy to use. Options:
            - "local": Entity-centric retrieval (for entity-specific questions)
            - "global": Relationship-centric retrieval (for pattern questions)
            - "hybrid": Combines local + global (for complex questions)
            - "naive": Traditional vector similarity (no graph structure)
            - "self": No retrieval, LLM uses only its knowledge
            Defaults to the configured default strategy.

    Returns:
        KnwlAnswer: Contains the answer text, context used, and metadata

    Raises:
        ValueError: If question is empty or invalid

    Example:
        >>> answer = await ask_question(
        ...     "What is photosynthesis?",
        ...     strategy="hybrid"
        ... )
        >>> print(answer.answer)
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")

    if strategy is None:
        strategy = KnwlParams.model_fields["strategy"].default

    logger.info(f"Processing question with strategy '{strategy}': {question[:100]}...")

    try:
        knwl_input = KnwlInput(text=question, params=KnwlParams(strategy=strategy))
        answer = await knwl.ask(knwl_input)

        logger.info(f"Answer generated successfully using strategy '{strategy}'")
        return answer

    except Exception as e:
        logger.error(f"Failed to answer question: {str(e)}", exc_info=True)
        raise


async def augment(text: str, strategy: Optional[str] = None) -> KnwlContext:
    """
    Augment text with relevant context from the knowledge graph.

    This function retrieves context WITHOUT generating an answer,
    making it ideal for custom RAG pipelines where you want to:
    - Use your own LLM configuration
    - Apply custom prompt templates
    - Combine multiple retrieval strategies
    - Cache and reuse context

    Args:
        text: The text/question to augment (required, non-empty)
        strategy: Graph RAG strategy to use. Options:
            - "local": Entity-centric retrieval
            - "global": Relationship-centric retrieval
            - "hybrid": Combines local + global (recommended)
            - "naive": Traditional vector similarity only
            - "self": No retrieval (returns empty context)
            Defaults to the configured default strategy.

    Returns:
        KnwlContext: Contains:
            - nodes: Relevant entities from the graph
            - edges: Relevant relationships from the graph
            - chunks: Relevant text chunks from vector store
            - metadata: Strategy info and retrieval stats

    Raises:
        ValueError: If text is empty or invalid

    Example:
        >>> context = await augment(
        ...     "Explain neural networks",
        ...     strategy="hybrid"
        ... )
        >>> print(f"Retrieved {len(context.nodes)} entities")
        >>> print(f"Retrieved {len(context.texts)} text chunks")
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    if strategy is None:
        strategy = KnwlParams.model_fields["strategy"].default

    logger.info(f"Augmenting text with strategy '{strategy}': {text[:100]}...")

    try:
        knwl_input = KnwlInput(
            text=text, params=KnwlParams(strategy=strategy, return_chunks=True)
        )
        context = await knwl.augment(knwl_input)

        logger.info(
            f"Context retrieved: {len(context.nodes)} nodes, "
            f"{len(context.edges)} edges, {len(context.texts)} chunks "
            f"(strategy: {strategy})"
        )
        return context

    except Exception as e:
        logger.error(f"Failed to augment text: {str(e)}", exc_info=True)
        raise


async def find_node_by_name(name: str, amount: int = 10) -> Optional[KnwlNode]:
    """
    Find a node in the knowledge graph by its name.

    Args:
        name: The name of the node to search for
    Returns:
        KnwlNode if found, None otherwise
    Example:
        >>> node = await find_node_by_name("Einstein")
        >>> if node:
        >>>     print(f"Found node: {node.name} ({node.type})")
    """
    try:
        logger.debug(f"Searching for node by name: {name}")
        nodes = await knwl.find_nodes(name, amount)

        return nodes

    except Exception as e:
        logger.error(f"Error finding node by name {name}: {str(e)}", exc_info=True)
        raise

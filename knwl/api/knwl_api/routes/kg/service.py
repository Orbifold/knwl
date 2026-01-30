"""
Knowledge Graph Service Layer

This module provides business logic for knowledge graph operations,
including background job processing, CRUD operations, and RAG queries.
"""
import time
from typing import Optional

from knwl import Knwl, KnwlInput, KnwlParams, KnwlAnswer, KnwlContext
from knwl.api.knwl_api.models.JobStatus import JobStatus, JobState
from knwl.api.knwl_api.taskiq_broker import broker
from knwl.models import KnwlDocument, KnwlNode
from knwl.models.KnwlFact import KnwlFact

# Initialize Knwl instance with default namespace
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
    """
    doc = KnwlDocument(**doc_data)
    started_at = time.time()
    result = await knwl.ingest(doc)
    finished_at = time.time()
    result_dict = result.model_dump(mode="json")
    result_dict["started_at"] = started_at
    result_dict["finished_at"] = finished_at
    result_dict["job_type"] = "ingest"
    return result_dict


@broker.task
async def process_extract_job(doc_data: dict) -> dict:
    """
    Background task to process data extraction.

    Extracts entities and relationships from a document without storing them.

    Args:
        doc_data: Dictionary representation of KnwlDocument

    Returns:
        Dict containing extraction results and timing information
    """
    doc = KnwlDocument(**doc_data)
    started_at = time.time()
    result = await knwl.extract(doc)
    finished_at = time.time()
    result_dict = result.model_dump(mode="json")
    result_dict["started_at"] = started_at
    result_dict["finished_at"] = finished_at
    result_dict["job_type"] = "extract"
    return result_dict


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
    """
    fact = KnwlFact(**fact_data)
    started_at = time.time()
    result = await knwl.add_fact(name=fact.name, content=fact.content, type=fact.type, id=fact.id)
    finished_at = time.time()
    result_dict = result.model_dump(mode="json")
    result_dict["started_at"] = started_at
    result_dict["finished_at"] = finished_at
    result_dict["job_type"] = "fact"
    return result_dict


async def add_job(job_type: str, data: dict) -> str:
    """
    Add a new job to the TaskIQ queue.

    Args:
        job_type: Type of job to create ("ingest", "fact", or "extract")
        data: Job data (KnwlDocument or KnwlFact as dict)

    Returns:
        str: The unique job ID for tracking

    Raises:
        ValueError: If job_type is not recognized
    """
    if job_type == "ingest":
        task = await process_ingest_job.kiq(data)
    elif job_type == "fact":
        task = await process_fact_job.kiq(data)
    elif job_type == "extract":
        task = await process_extract_job.kiq(data)
    else:
        raise ValueError(f"Unknown job type: {job_type}. Must be 'ingest', 'fact', or 'extract'.")

    return task.task_id


async def get_job_status(job_id: str) -> Optional[JobStatus]:
    """
    Retrieve the status of a given job.

    Args:
        job_id: The unique identifier of the job

    Returns:
        JobStatus if found, None otherwise
    """
    if broker.result_backend is None:
        return None

    try:
        result = await broker.result_backend.get_result(job_id)
    except Exception:
        return None

    if result is None:
        return None

    # Map TaskIQ state to our JobState
    if result.is_err:
        state = JobState.FAILED
        error = str(result.error) if result.error else "Unknown error"
        job_result = None
        started_at = 0
        finished_at = 0
        job_type = "Unknown"
    elif result.return_value is not None:
        state = JobState.COMPLETED
        error = None
        job_result = result.return_value
        started_at = job_result.get("started_at", 0)
        finished_at = job_result.get("finished_at", 0)
        job_type = job_result.get("job_type", "Unknown")
    else:
        # Task exists but no result yet - it's either pending or running
        state = JobState.RUNNING
        error = None
        job_result = None
        started_at = 0
        finished_at = 0
        job_type = "Unknown"

    return JobStatus(
        job_id=job_id,
        state=state,
        result=job_result,
        error=error,
        started_at=started_at,
        finished_at=finished_at,
        job_type=job_type
    )


async def node_count() -> int:
    """
    Get the total number of nodes in the knowledge graph.

    Returns:
        int: The count of nodes
    """
    return await knwl.node_count()


async def edge_count() -> int:
    """
    Get the total number of edges in the knowledge graph.

    Returns:
        int: The count of edges
    """
    return await knwl.edge_count()


async def get_namespace() -> str:
    """
    Get the current namespace of the knowledge graph.

    Returns:
        str: The namespace identifier
    """
    return knwl.namespace


async def get_node_by_id(id: str) -> Optional[KnwlNode]:
    """
    Retrieve a node by its unique identifier.

    Args:
        id: The unique identifier of the node

    Returns:
        KnwlNode if found, None otherwise
    """
    return await knwl.get_node_by_id(id)


async def delete_node_by_id(id: str) -> Optional[bool]:
    """
    Delete a node by its unique identifier.

    Args:
        id: The unique identifier of the node to delete

    Returns:
        bool indicating success, or None if node not found
    """
    return await knwl.delete_node_by_id(id)


async def ask_question(question: str, strategy: Optional[str] = None) -> KnwlAnswer:
    """
    Ask a question to the knowledge graph and generate an answer.

    This function retrieves relevant context using Graph RAG and
    generates an LLM-based answer.

    Args:
        question: The question to ask
        strategy: Graph RAG strategy to use (local, global, hybrid, naive, self).
                 Defaults to the configured default strategy.

    Returns:
        KnwlAnswer: Contains the answer, context, and metadata
    """
    if strategy is None:
        strategy = KnwlParams.model_fields["strategy"].default

    knwl_input = KnwlInput(text=question, params=KnwlParams(strategy=strategy))
    return await knwl.ask(knwl_input)


async def augment(text: str, strategy: Optional[str] = None) -> KnwlContext:
    """
    Augment text with relevant context from the knowledge graph.

    This function retrieves context without generating an answer,
    making it ideal for custom RAG pipelines.

    Args:
        text: The text/question to augment
        strategy: Graph RAG strategy to use (local, global, hybrid, naive, self).
                 Defaults to the configured default strategy.

    Returns:
        KnwlContext: Contains nodes, edges, chunks, and metadata
    """
    if strategy is None:
        strategy = KnwlParams.model_fields["strategy"].default

    knwl_input = KnwlInput(text=text, params=KnwlParams(strategy=strategy, return_chunks=True))
    return await knwl.augment(knwl_input)

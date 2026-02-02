import time
from enum import Enum
from typing import Optional

import pymupdf4llm
from knwl.api.knwl_api.taskiq_broker import broker
from knwl import (
    Knwl,
    KnwlInput,
    KnwlParams,
    KnwlAnswer,
    KnwlContext,
    KnwlDocument,
    KnwlFact,
)

from knwl.api.knwl_api.models.JobStatus import JobStatus, JobState
from knwl.logging import log


class JobType(str, Enum):
    """Enumeration of supported background job types."""

    INGEST = "ingest"
    EXTRACT = "extract"
    FACT = "fact"


# Initialize Knwl instance with default namespace
# This is a singleton shared across all requests
knwl = Knwl()

@broker.task
async def parse_pdf_to_markdown(file_path: str, page_number: int = None) -> str:
    """
    Background task to parse a PDF file and extract its content as Markdown.

    Args:
        file_path: Path to the PDF file to be parsed
        page_number: Optional specific page number to extract
    Returns:
        Extracted Markdown content as a string
    """
    page_number_list=None
    if not (page_number is None):
        page_number_list= [page_number]   
    
    md =  pymupdf4llm.to_markdown(file_path, pages=page_number_list)
    return md

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
        log.info(
            f"Starting ingestion job for document: {doc_data.get('name', 'unnamed')}"
        )
        doc = KnwlDocument(**doc_data)
        result = await knwl.ingest(doc)

        finished_at = time.time()
        duration = finished_at - started_at

        log.info(f"Ingestion completed in {duration:.2f}s for: {doc.name}")

        result_dict = result.model_dump(mode="json")
        result_dict["started_at"] = started_at
        result_dict["finished_at"] = finished_at
        result_dict["duration"] = duration
        result_dict["job_type"] = JobType.INGEST.value

        return result_dict

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        log.error(f"Ingestion failed after {duration:.2f}s: {str(e)}")
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
        log.info(
            f"Starting extraction job for document: {doc_data.get('name', 'unnamed')}"
        )
        doc = KnwlDocument(**doc_data)
        result = await knwl.extract(doc)

        finished_at = time.time()
        duration = finished_at - started_at

        log.info(f"Extraction completed in {duration:.2f}s for: {doc.name}")

        result_dict = result.model_dump(mode="json")
        result_dict["started_at"] = started_at
        result_dict["finished_at"] = finished_at
        result_dict["duration"] = duration
        result_dict["job_type"] = JobType.EXTRACT.value

        return result_dict

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        log.error(f"Extraction failed after {duration:.2f}s: {str(e)}")
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
        log.info(f"Starting fact addition job for: {fact_data.get('name', 'unnamed')}")
        fact = KnwlFact(**fact_data)
        result = await knwl.add_fact(
            name=fact.name, content=fact.content, type=fact.type, id=fact.id
        )

        finished_at = time.time()
        duration = finished_at - started_at

        log.info(f"Fact addition completed in {duration:.2f}s for: {fact.name}")

        result_dict = result.model_dump(mode="json")
        result_dict["started_at"] = started_at
        result_dict["finished_at"] = finished_at
        result_dict["duration"] = duration
        result_dict["job_type"] = JobType.FACT.value

        return result_dict

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        log.error(
            f"Fact addition failed after {duration:.2f}s: {str(e)}"
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
    log.debug(f"Creating {job_type} job")

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

    log.info(f"Job created with ID: {task.task_id} (type: {job_type})")
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
        log.warning("Result backend not configured - cannot retrieve job status")
        return None

    try:
        result = await broker.result_backend.get_result(job_id)
    except Exception as e:
        log.error(f"Error retrieving job status for {job_id}: {str(e)}")
        return None

    if result is None:
        log.debug(f"Job not found: {job_id}")
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

        log.warning(f"Job {job_id} failed: {error}")

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

        log.debug(f"Job {job_id} completed in {duration:.2f}s")

    else:
        # Task exists but no result yet - it's either pending or running
        state = JobState.RUNNING
        error = None
        job_result = None
        started_at = 0
        finished_at = 0
        job_type = "Unknown"

        log.debug(f"Job {job_id} is still running")

    return JobStatus(
        job_id=job_id,
        state=state,
        result=job_result,
        error=error,
        started_at=started_at,
        finished_at=finished_at,
        job_type=job_type,
    )

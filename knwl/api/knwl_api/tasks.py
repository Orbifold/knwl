import asyncio
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
from knwl.api.knwl_api.models.JobResult import JobResult
from knwl.logging import log


class JobType(str, Enum):
    """Enumeration of supported background job types."""

    INGEST = "ingest"
    EXTRACT = "extract"
    FACT = "fact"
    DUMMY = "dummy"
    PARSE = "parse"


# Initialize Knwl instance with default namespace
# This is a singleton shared across all requests
knwl = Knwl()

@broker.task
async def parse_pdf_to_markdown(file_path: str, page_number: int = None, save_document: bool = False) -> JobResult:
    """
    Background task to parse a PDF file and extract its content as Markdown.

    Args:
        file_path: Path to the PDF file to be parsed
        page_number: Optional specific page number to extract
        save_document: Whether to use the document storage system to save the document
    Returns:
        Extracted Markdown content and optionally the document as a dict
    """
    page_number_list=None
    if not (page_number is None):
        page_number_list= [page_number]   
    
    md =  pymupdf4llm.to_markdown(file_path, pages=page_number_list)
    started_at = time.time()
    if save_document:
        name = file_path.split("/")[-1]
        # remove extension
        name = name.rsplit(".", 1)[0]
        doc = KnwlDocument(
            name=name,
            content=md,
            description=f"Parsed from PDF file: {file_path}",
        )
        doc_dict = await knwl.save_document(doc)
        output = {"markdown": md, "document": doc.id}
    else:
        output = {"markdown": md, "document": None}

    finished_at = time.time()
    duration = finished_at - started_at

    job_res = JobResult(
        job_type=JobType.PARSE.value,
        started_at=started_at,
        finished_at=finished_at,
        duration=duration,
        output=output,
    )

    return job_res.model_dump()

@broker.task
async def process_ingest_job(doc_data: dict) -> JobResult:
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

        output = result.model_dump(mode="json")
        job_res = JobResult(
            job_type=JobType.INGEST.value,
            started_at=started_at,
            finished_at=finished_at,
            duration=duration,
            output=output,
        )

        # Return a JSON-serializable form for the TaskIQ result backend
        return job_res.model_dump()

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        log.error(f"Ingestion failed after {duration:.2f}s: {str(e)}")
        raise


@broker.task
async def process_extract_job(doc_data: dict) -> JobResult:
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

        output = result.model_dump(mode="json")
        job_res = JobResult(
            job_type=JobType.EXTRACT.value,
            started_at=started_at,
            finished_at=finished_at,
            duration=duration,
            output=output,
        )

        return job_res.model_dump()

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        log.error(f"Extraction failed after {duration:.2f}s: {str(e)}")
        raise


@broker.task
async def process_fact_job(fact_data: dict) -> JobResult:
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

        output = result.model_dump(mode="json")
        job_res = JobResult(
            job_type=JobType.FACT.value,
            started_at=started_at,
            finished_at=finished_at,
            duration=duration,
            output=output,
        )

        return job_res.model_dump()

    except Exception as e:
        finished_at = time.time()
        duration = finished_at - started_at
        log.error(
            f"Fact addition failed after {duration:.2f}s: {str(e)}"
        )
        raise
@broker.task
async def dummy_job(name:str, delay_seconds: int = 5) -> JobResult:
    """
    A simple dummy job that waits for a specified duration.

    Args:
        delay_seconds: Number of seconds to wait
    Returns:
        JobResult containing job timing information
    """
    started_at = time.time()
    log.info(f"Starting dummy job '{name}' with {delay_seconds}s delay")
    await asyncio.sleep(delay_seconds)
    finished_at = time.time()
    duration = finished_at - started_at
    log.info(f"Dummy job '{name}' completed in {duration:.2f}s")
    job_res = JobResult(
        job_type=JobType.DUMMY.value,
        started_at=started_at,
        finished_at=finished_at,
        duration=duration,
        output=f"Dummy job '{name}'",
    )
    return job_res.model_dump()

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
    elif job_type == JobType.DUMMY.value:
        task = await dummy_job.kiq(**data)
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
        raw = result.return_value
        try:
            if isinstance(raw, dict):
                jr = JobResult(**raw)
            elif isinstance(raw, JobResult):
                jr = raw
            else:
                jr = JobResult(**dict(raw))
        except Exception:
            # Fall back to treating the return as a plain dict
            jr = None

        if jr is not None:
            job_result = jr.output
            started_at = jr.started_at
            finished_at = jr.finished_at
            job_type = jr.job_type
            duration = jr.duration
        else:
            # Last-resort fallback to previous behavior
            job_result = raw
            started_at = raw.get("started_at", 0)
            finished_at = raw.get("finished_at", 0)
            job_type = raw.get("job_type", "Unknown")
            duration = raw.get("duration", finished_at - started_at if finished_at else 0)

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

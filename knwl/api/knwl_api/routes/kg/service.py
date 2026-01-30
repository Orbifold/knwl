import time

from knwl import Knwl, KnwlInput, KnwlParams, KnwlAnswer, KnwlContext
from knwl.api.knwl_api.models.JobStatus import JobStatus, JobState
from knwl.api.knwl_api.taskiq_broker import broker
from knwl.models import KnwlDocument
from knwl.models.KnwlFact import KnwlFact

knwl = Knwl()  # Initialize Knwl instance with default namespace


@broker.task
async def process_ingest_job(doc_data: dict) -> dict:
    """Background task to process data ingestion"""
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
    """Background task to process data extraction"""
    doc = KnwlDocument(**doc_data)
    started_at = time.time()
    result = await knwl.extract(doc)
    finished_at = time.time()
    result_dic = result.model_dump(mode="json")
    result_dic["started_at"] = started_at
    result_dic["finished_at"] = finished_at
    result_dic["job_type"] = "extract"
    return result_dic


@broker.task
async def process_fact_job(fact_data: dict) -> dict:
    """Background task to process adding a fact"""
    fact = KnwlFact(**fact_data)
    started_at = time.time()
    result = await knwl.add_fact(name=fact.name, content=fact.content, type=fact.type, id=fact.id)
    finished_at = time.time()
    result_dic = result.model_dump(mode="json")
    result_dic["started_at"] = started_at
    result_dic["finished_at"] = finished_at
    result_dic["job_type"] = "fact"
    return result_dic


async def add_job(job_type: str, data: dict) -> str:
    """Adds a new job to the TaskIQ queue"""
    if job_type == "ingest":
        task = await process_ingest_job.kiq(data)
    elif job_type == "fact":
        task = await process_fact_job.kiq(data)
    elif job_type == "extract":
        task = await process_extract_job.kiq(data)
    else:
        raise ValueError(f"Unknown job type: {job_type}")

    return task.task_id


async def get_job_status(job_id: str) -> JobStatus | None:
    """Retrieves the status of a given job"""
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
        finished_at = 0
        job_type = "Unknown"
    else:
        # Task exists but no result yet - it's either pending or running
        state = JobState.RUNNING
        error = None
        job_result = None
        started_at = 0
        finished_at = 0
        job_type = "Unknown"

    return JobStatus(job_id=job_id, state=state, result=job_result, error=error, started_at=started_at, finished_at=finished_at, job_type=job_type, )


async def node_count() -> int:
    """Returns the count of nodes in the knowledge graph."""
    return await knwl.node_count()


async def edge_count() -> int:
    """Returns the count of edges in the knowledge graph."""
    return await knwl.edge_count()


async def get_namespace() -> str:
    """Returns the current namespace of the knowledge graph."""
    return knwl.namespace


async def get_node_by_id(id: str):
    """Retrieves a node by its Id."""
    return await knwl.get_node_by_id(id)


async def delete_node_by_id(id: str):
    """Deletes a node by its Id."""
    return await knwl.delete_node_by_id(id)


async def ask_question(question: str, strategy: str = None) -> KnwlAnswer:
    """
    Asks a question to the knowledge graph.
    """
    if strategy is None:
        strategy = KnwlParams.model_fields["strategy"].default
    input = KnwlInput(text=question, params=KnwlParams(strategy=strategy))
    return await knwl.ask(input)


async def augment(text: str, strategy: str = None) -> KnwlContext:
    """
    Augments the given text using the knowledge graph.
    """
    if strategy is None:
        strategy = KnwlParams.model_fields["strategy"].default
    input = KnwlInput(text=text, params=KnwlParams(strategy=strategy, return_chunks=True))
    return await knwl.augment(input)

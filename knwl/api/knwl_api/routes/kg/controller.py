from fastapi import APIRouter, HTTPException
from fastapi import Request
from knwl import KnwlParams, KnwlAnswer, KnwlContext

from knwl.api.knwl_api.models.JobStatus import JobStatus, JobResponse
from knwl.models import KnwlDocument
from knwl.models.KnwlFact import KnwlFact
from knwl.api.knwl_api.routes.kg import service

router = APIRouter()


@router.get("/node_count", description="Returns the amount of nodes.")
async def get_node_count(request: Request):
    try:
        return await service.node_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edge_count", description="Returns the amount of edges.")
async def get_edge_count(request: Request):
    try:
        return await service.edge_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namespace", description="Returns the current namespace.")
async def get_namespace(request: Request):
    try:
        return await service.get_namespace()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{id}", description="Retrieves a node by its Id.")
async def get_node_by_id(id: str):
    try:
        node = await service.get_node_by_id(id)
        return node
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/node/{id}", description="Deletes a node by its Id.")
async def delete_node_by_id(id: str):
    try:
        return await service.delete_node_by_id(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", description="Ingests data into the knowledge graph.", response_model=JobResponse)
async def ingest_data(doc:KnwlDocument):
    """
    Ingests data into the knowledge graph.
    Expects a JSON body with a 'text' field, optionally 'name', 'description'.
    """
    try:

        job_id = await service.add_job("ingest", doc.model_dump())

        return JobResponse(job_id=job_id, message="Ingestion job started successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", description="Extracts data into the knowledge graph.", response_model=JobResponse)
async def extract_data(doc:KnwlDocument):
    """
    Extracts data into the knowledge graph.
    Expects a JSON body with a 'text' field, optionally 'name', 'description'.
    """
    try:

        job_id = await service.add_job("extract", doc.model_dump())

        return JobResponse(job_id=job_id, message="Extraction job started successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}", description="Get the status of a job.", response_model=JobStatus)
async def get_job_status(job_id: str):
    try:
        status = await service.get_job_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fact", description="Adds a fact to the knowledge graph.", response_model=JobResponse)
async def add_fact(fact: KnwlFact):
    """
    Adds a fact to the knowledge graph.
    """
    try:
        job_id = await service.add_job("fact", fact.model_dump())
        return JobResponse(job_id=job_id, message="Fact job started successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", description="Ask a question.", response_model=KnwlAnswer)
async def ask_question(request: Request):
    """
    Asks a question to the knowledge graph.
    Expects a JSON body with a 'question' field and, optionally, a 'strategy' field.
    Note: this is just a utility, you likely benefit more from the augment method in your RAG flow.
    """
    try:
        data = await request.json()
        if not "question" in data:
            raise HTTPException(status_code=400, detail="Missing 'question' field in request body")
        if not "strategy" in data:
            data["strategy"] = KnwlParams.model_fields["strategy"].default
        answer = await service.ask_question(data["question"], data["strategy"])

        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/augment", description="Graph augmentation of the given question.", response_model=KnwlContext)
async def augment_text(request: Request):
    """
    Augments the given text using the knowledge graph.
    Expects a JSON body with a 'question' field and, optionally, a 'strategy' field.
    """
    try:
        data = await request.json()
        if not "question" in data:
            raise HTTPException(status_code=400, detail="Missing 'question' field in request body")
        if not "strategy" in data:
            data["strategy"] = KnwlParams.model_fields["strategy"].default
        context = await service.augment(data["question"], data["strategy"])
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

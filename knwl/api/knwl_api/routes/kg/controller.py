"""
Knowledge Graph API Controller

This module provides FastAPI endpoints for interacting with the Knwl knowledge graph,
including CRUD operations on nodes, data ingestion, extraction, and RAG queries.
"""

from typing import Dict

from fastapi import APIRouter, HTTPException, status
from knwl import KnwlAnswer, KnwlContext
from knwl.models import KnwlDocument, KnwlNode
from knwl.models.KnwlFact import KnwlFact
from pydantic import BaseModel, Field

from knwl.api.knwl_api.models.JobStatus import JobStatus, JobResponse
from knwl.api.knwl_api.routes.kg import service

router = APIRouter()


class QuestionRequest(BaseModel):
    """Request model for asking questions or augmenting text."""

    question: str = Field(
        ..., description="The question or text to process", min_length=1
    )
    strategy: str | None = Field(
        None, description="Graph RAG strategy (local, global, hybrid, naive, self)"
    )


class CountResponse(BaseModel):
    """Response model for count endpoints."""

    count: int = Field(..., description="The count value")


class NamespaceResponse(BaseModel):
    """Response model for namespace endpoint."""

    namespace: str = Field(..., description="The current namespace")


@router.get(
    "/node_count",
    response_model=CountResponse,
    summary="Get node count",
    description="Returns the total number of nodes in the knowledge graph.",
    responses={
        200: {"description": "Successfully retrieved node count"},
        500: {"description": "Internal server error"},
    },
)
async def get_node_count() -> CountResponse:
    """
    Get the total number of nodes in the knowledge graph.

    Returns:
        CountResponse: Object containing the node count

    Raises:
        HTTPException: 500 error if the operation fails
    """
    try:
        count = await service.node_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve node count: {str(e)}",
        )


@router.get(
    "/edge_count",
    response_model=CountResponse,
    summary="Get edge count",
    description="Returns the total number of edges in the knowledge graph.",
    responses={
        200: {"description": "Successfully retrieved edge count"},
        500: {"description": "Internal server error"},
    },
)
async def get_edge_count() -> CountResponse:
    """
    Get the total number of edges in the knowledge graph.

    Returns:
        CountResponse: Object containing the edge count

    Raises:
        HTTPException: 500 error if the operation fails
    """
    try:
        count = await service.edge_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve edge count: {str(e)}",
        )


@router.get(
    "/namespace",
    response_model=NamespaceResponse,
    summary="Get current namespace",
    description="Returns the current namespace of the knowledge graph.",
    responses={
        200: {"description": "Successfully retrieved namespace"},
        500: {"description": "Internal server error"},
    },
)
async def get_namespace() -> NamespaceResponse:
    """
    Get the current namespace of the knowledge graph.

    Returns:
        NamespaceResponse: Object containing the namespace

    Raises:
        HTTPException: 500 error if the operation fails
    """
    try:
        namespace = await service.get_namespace()
        return NamespaceResponse(namespace=namespace)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve namespace: {str(e)}",
        )


@router.get(
    "/node/{id}",
    response_model=KnwlNode,
    summary="Get node by ID",
    description="Retrieves a specific node from the knowledge graph by its ID.",
    responses={
        200: {"description": "Successfully retrieved node"},
        404: {"description": "Node not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_node_by_id(id: str) -> KnwlNode:
    """
    Retrieve a node by its unique identifier.

    Args:
        id: The unique identifier of the node

    Returns:
        KnwlNode: The requested node object

    Raises:
        HTTPException: 404 if node not found, 500 if operation fails
    """
    try:
        node = await service.get_node_by_id(id)
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with ID '{id}' not found",
            )
        return node
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve node: {str(e)}",
        )


@router.delete(
    "/node/{id}",
    summary="Delete node by Id",
    description="Deletes a specific node from the knowledge graph by its Id.",
    responses={
        200: {"description": "Successfully deleted node"},
        404: {"description": "Node not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_node_by_id(id: str) -> Dict[str, str]:
    """
    Delete a node by its unique identifier.

    Args:
        id: The unique identifier of the node to delete

    Returns:
        Dict containing deletion confirmation message

    Raises:
        HTTPException: 404 if node not found, 500 if operation fails
    """
    try:
        result = await service.delete_node_by_id(id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with Id '{id}' not found",
            )
        return {"message": f"Node '{id}' deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete node: {str(e)}",
        )


@router.post(
    "/ingest",
    response_model=JobResponse,
    summary="Ingest document",
    description="Ingests a document into the knowledge graph (async scheduled job).",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Ingestion job accepted and queued"},
        400: {"description": "Invalid document data"},
        500: {"description": "Internal server error"},
    },
)
async def ingest_data(doc: KnwlDocument) -> JobResponse:
    """
    Ingest a document into the knowledge graph.

    This creates a background job that will:
    1. Chunk the document text
    2. Extract entities and relationships
    3. Store in the graph and vector database

    Args:
        doc: KnwlDocument containing text, name, and metadata

    Returns:
        JobResponse: Contains job_id for tracking the ingestion progress

    Raises:
        HTTPException: 400 for invalid data, 500 if job creation fails
    """
    try:
        job_id = await service.add_job("ingest", doc.model_dump())
        return JobResponse(job_id=job_id, message="Ingestion job started successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ingestion job: {str(e)}",
        )


@router.post(
    "/extract",
    response_model=JobResponse,
    summary="Extract graph from document",
    description="Extracts entities and relationships from a document (async scheduled job).",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Extraction job accepted and queued"},
        400: {"description": "Invalid document data"},
        500: {"description": "Internal server error"},
    },
)
async def extract_data(doc: KnwlDocument) -> JobResponse:
    """
    Extract entities and relationships from a document.

    This creates a background job that will:
    1. Analyze the document text using LLM
    2. Extract entities (nodes) and relationships (edges)
    3. Return the graph structure without storing it

    Args:
        doc: KnwlDocument containing text to extract from

    Returns:
        JobResponse: Contains job_id for tracking the extraction progress

    Raises:
        HTTPException: 400 for invalid data, 500 if job creation fails
    """
    try:
        job_id = await service.add_job("extract", doc.model_dump())
        return JobResponse(job_id=job_id, message="Extraction job started successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start extraction job: {str(e)}",
        )


@router.get(
    "/job/{job_id}",
    response_model=JobStatus,
    summary="Get job status",
    description="Retrieves the status and result of a background job.",
    responses={
        200: {"description": "Successfully retrieved job status"},
        404: {"description": "Job not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_job_status(job_id: str) -> JobStatus:
    """
    Get the status of a background job.

    Use this endpoint to check the progress of ingest, extract, or fact jobs.

    Args:
        job_id: The unique identifier of the job (returned from POST endpoints)

    Returns:
        JobStatus: Contains state (PENDING/RUNNING/COMPLETED/FAILED), result, and timing info

    Raises:
        HTTPException: 404 if job not found, 500 if operation fails
    """
    try:
        job_status = await service.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found",
            )
        return job_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}",
        )


@router.post(
    "/fact",
    response_model=JobResponse,
    summary="Add fact to graph",
    description="Adds a single fact to the knowledge graph (async scheduled job).",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Fact job accepted and queued"},
        400: {"description": "Invalid fact data"},
        500: {"description": "Internal server error"},
    },
)
async def add_fact(fact: KnwlFact) -> JobResponse:
    """
    Add a fact to the knowledge graph.

    A fact is a simple piece of knowledge with a name and content.
    The system will extract entities and relationships from the fact.

    Args:
        fact: KnwlFact containing name, content, type, and optional ID

    Returns:
        JobResponse: Contains job_id for tracking the fact addition progress

    Raises:
        HTTPException: 400 for invalid data, 500 if job creation fails
    """
    try:
        job_id = await service.add_job("fact", fact.model_dump())
        return JobResponse(job_id=job_id, message="Fact job started successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start fact job: {str(e)}",
        )


@router.post(
    "/ask",
    response_model=KnwlAnswer,
    summary="Ask a question",
    description="Asks a question to the knowledge graph and returns an LLM-generated answer.",
    responses={
        200: {"description": "Successfully generated answer"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def ask_question(request: QuestionRequest) -> KnwlAnswer:
    """
    Ask a question to the knowledge graph.

    This endpoint:
    1. Retrieves relevant context using the specified Graph RAG strategy
    2. Generates an answer using the LLM with the retrieved context

    Note: For most RAG applications, use the /augment endpoint instead
    to get just the context and generate answers in your own application.

    Args:
        request: QuestionRequest containing question and optional strategy

    Returns:
        KnwlAnswer: Contains the answer text, context used, and metadata

    Raises:
        HTTPException: 400 for invalid request, 500 if operation fails
    """
    try:
        answer = await service.ask_question(request.question, request.strategy)
        return answer
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}",
        )


@router.post(
    "/augment",
    response_model=KnwlContext,
    summary="Augment text with graph context",
    description="Retrieves relevant context from the knowledge graph for the given question.",
    responses={
        200: {"description": "Successfully retrieved context"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def augment_text(request: QuestionRequest) -> KnwlContext:
    """
    Augment a question/text with relevant context from the knowledge graph.

    This is the core Graph RAG endpoint. It:
    1. Analyzes the question to extract keywords/entities
    2. Retrieves relevant nodes, edges, and text chunks using the specified strategy
    3. Returns the context WITHOUT generating an answer

    Use this in your own RAG pipeline to get context, then generate
    answers using your preferred LLM configuration.

    Available strategies:
    - local: Entity-centric retrieval (good for specific entity questions)
    - global: Relationship-centric retrieval (good for relationship questions)
    - hybrid: Combines local + global (best for complex questions)
    - naive: Traditional vector similarity (no graph structure)
    - self: No retrieval, LLM uses its own knowledge

    Args:
        request: QuestionRequest containing question and optional strategy

    Returns:
        KnwlContext: Contains nodes, edges, chunks, and metadata

    Raises:
        HTTPException: 400 for invalid request, 500 if operation fails
    """
    try:
        context = await service.augment(request.question, request.strategy)
        return context
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to augment text: {str(e)}",
        )


@router.get(
    "/find/{name}",
    response_model=list[KnwlNode],
    summary="Find nodes by name",
    description="Retrieves nodes from the knowledge graph that match the given name.",
    responses={
        200: {"description": "Successfully retrieved nodes"},
        500: {"description": "Internal server error"},
    },
)
async def find_nodes_by_name(name: str) -> list[KnwlNode]:
    """
    Find nodes in the knowledge graph by their name.

    Args:
        name: The name of the nodes to search for
    Returns:
        List of KnwlNode objects that match the given name
    Raises:
        HTTPException: 500 error if the operation fails
    """
    try:
        nodes = await service.find_node_by_name(name)
        return nodes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve nodes: {str(e)}",
        )

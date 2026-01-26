"""
MCP Server for Knwl Knowledge Graph API

This module provides an MCP (Model Context Protocol) server interface
for the Knwl knowledge graph operations using FastMCP.
"""

import asyncio
from typing import Optional
from fastmcp import FastMCP

from knwl import KnwlInput, KnwlParams
from knwl.api.knwl_api.routes.kg import service


# Create MCP server
mcp = FastMCP("API Tools")

# Get the MCP app before creating FastAPI app
mcp_app = mcp.http_app()
# ============================================================================================
# Resources
# ============================================================================================
@mcp.resource("text://info", name="info")
def get_greeting() -> dict:
    """Returns info about the FastMCP Knwl API server."""
    return {
        "version": "1.0",
        "name": "Knwl Knowledge Graph MCP API",
        "description": "MCP API for Knwl Knowledge Graph operations"
    }
# ============================================================================================
# Tools
# ============================================================================================
@mcp.tool(name="node_count")
async def get_node_count() -> int:
    """
    Get the total number of nodes in the knowledge graph.

    Returns:
        The count of nodes in the graph
    """
    return await service.node_count()


@mcp.tool(name="edge_count")
async def get_edge_count() -> int:
    """
    Get the total number of edges in the knowledge graph.

    Returns:
        The count of edges in the graph
    """
    return await service.edge_count()


@mcp.tool(name="namespace")
async def get_namespace() -> str:
    """
    Get the current namespace of the knowledge graph.

    Returns:
        The namespace string
    """
    return await service.get_namespace()


@mcp.tool()
async def get_node(node_id: str) -> dict:
    """
    Retrieve a node from the knowledge graph by its ID.

    Args:
        node_id: The unique identifier of the node

    Returns:
        The node data as a dictionary
    """
    return await service.get_node_by_id(node_id)


@mcp.tool()
async def delete_node(node_id: str) -> dict:
    """
    Delete a node from the knowledge graph by its ID.

    Args:
        node_id: The unique identifier of the node to delete

    Returns:
        Result of the deletion operation
    """
    return await service.delete_node_by_id(node_id)


@mcp.tool(name="ingest")
async def ingest_text(
    text: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Ingest text data into the knowledge graph. This creates a background job
    that processes the text and extracts knowledge graph entities and relationships.

    Args:
        text: The text content to ingest
        name: Optional name for the ingestion
        description: Optional description for the ingestion

    Returns:
        Job information including job_id and message
    """
    data = {"text": text}
    if name:
        data["name"] = name
    if description:
        data["description"] = description

    job_id = await service.add_job("ingest", data)
    return {
        "job_id": job_id,
        "message": "Ingestion job started successfully"
    }


@mcp.tool()
async def add_fact(
    name: str,
    content: str,
    fact_type: str = "Fact",
    fact_id: Optional[str] = None
) -> dict:
    """
    Add a fact to the knowledge graph. This creates a background job
    that processes and stores the fact.

    Args:
        name: The name of the fact
        content: The content of the fact
        fact_type: The type/category of the fact (default: "Fact")
        fact_id: Optional unique identifier for the fact

    Returns:
        Job information including job_id and message
    """
    data = {
        "name": name,
        "content": content,
        "type": fact_type
    }
    if fact_id:
        data["id"] = fact_id

    job_id = await service.add_job("fact", data)
    return {
        "job_id": job_id,
        "message": "Fact job started successfully"
    }


@mcp.tool()
async def get_job_status(job_id: str) -> dict:
    """
    Get the status of a background job (ingestion or fact addition).

    Args:
        job_id: The unique identifier of the job

    Returns:
        Job status including state, result, and error (if any)
    """
    status = await service.get_job_status(job_id)
    if status is None:
        return {
            "error": f"Job {job_id} not found"
        }
    return status.model_dump()


@mcp.tool()
async def ask_question(
    question: str,
    strategy: Optional[str] = None
) -> dict:
    """
    Ask a question to the knowledge graph and get an answer.

    Args:
        question: The question to ask
        strategy: Optional strategy for answering (e.g., 'default', 'precise', 'comprehensive')

    Returns:
        The answer from the knowledge graph
    """
    answer = await service.ask_question(question, strategy)
    return answer.model_dump()


@mcp.tool()
async def augment_text(
    text: str,
    strategy: Optional[str] = None
) -> dict:
    """
    Augment text with context from the knowledge graph for RAG applications.
    This retrieves relevant context that can be used to enhance LLM responses.

    Args:
        text: The text to augment
        strategy: Optional strategy for augmentation (e.g., 'default', 'precise', 'comprehensive')

    Returns:
        The augmented context from the knowledge graph
    """
    context = await service.augment(text, strategy)
    return context.model_dump()

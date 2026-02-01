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
from knwl.models import KnwlDocument, KnwlNode
from knwl.models.KnwlFact import KnwlFact
from knwl.logging import log
from knwl.api.knwl_api.tasks import knwl

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
        log.debug(f"Node count retrieved: {count}")
        return count
    except Exception as e:
        log.error(f"Failed to get node count: {str(e)}", exc_info=True)
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
        log.debug(f"Edge count retrieved: {count}")
        return count
    except Exception as e:
        log.error(f"Failed to get edge count: {str(e)}", exc_info=True)
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
        log.debug(f"Retrieving node: {id}")
        node = await knwl.get_node_by_id(id)

        if node:
            log.debug(f"Node found: {node.name} (type: {node.type})")
        else:
            log.debug(f"Node not found: {id}")

        return node

    except Exception as e:
        log.error(f"Error retrieving node {id}: {str(e)}", exc_info=True)
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
        log.info(f"Deleting node: {id}")
        result = await knwl.delete_node_by_id(id)

        if result:
            log.info(f"Node deleted successfully: {id}")
        else:
            log.warning(f"Node not found for deletion: {id}")

        return result

    except Exception as e:
        log.error(f"Error deleting node {id}: {str(e)}", exc_info=True)
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

    log.info(f"Processing question with strategy '{strategy}': {question[:100]}...")

    try:
        knwl_input = KnwlInput(text=question, params=KnwlParams(strategy=strategy))
        answer = await knwl.ask(knwl_input)

        log.info(f"Answer generated successfully using strategy '{strategy}'")
        return answer

    except Exception as e:
        log.error(f"Failed to answer question: {str(e)}", exc_info=True)
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

    log.info(f"Augmenting text with strategy '{strategy}': {text[:100]}...")

    try:
        knwl_input = KnwlInput(
            text=text, params=KnwlParams(strategy=strategy, return_chunks=True)
        )
        context = await knwl.augment(knwl_input)

        log.info(
            f"Context retrieved: {len(context.nodes)} nodes, "
            f"{len(context.edges)} edges, {len(context.texts)} chunks "
            f"(strategy: {strategy})"
        )
        return context

    except Exception as e:
        log.error(f"Failed to augment text: {str(e)}", exc_info=True)
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
        log.debug(f"Searching for node by name: {name}")
        nodes = await knwl.find_nodes(name, amount)

        return nodes

    except Exception as e:
        log.error(f"Error finding node by name {name}: {str(e)}", exc_info=True)
        raise

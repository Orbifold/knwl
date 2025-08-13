from dataclasses import dataclass


@dataclass(frozen=True)
class KnwlRagReference:
    """
    Represents a reference in the RAG (Retrieval-Augmented Generation) system.
    This class holds metadata about a reference, including its index, name, description,
    timestamp, and a unique identifier (id).
    It is used to track and manage references within the context of RAG operations.

    Chunks refer to specific pieces of information or data that are retrieved
    during the RAG process, and references provide additional context or metadata
    about these chunks.
    The `id` is typically a hash of the reference's content, ensuring uniqueness.
    """
    index: str
    name: str
    description: str
    timestamp: str
    id: str

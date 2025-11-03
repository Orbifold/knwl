from datetime import datetime
from typing import Callable
from pydantic import BaseModel, Field
from rich.text import Text

from knwl.models.KnwlContext import KnwlContext

# @deprecated("V1 remnant - use KnwlAnswer instead.")  # requires Python 3.13+
class KnwlResponse(BaseModel):
    """
    Represents a response from the KNWL system containing the answer, context, and performance metrics.
    
    Attributes:
        question (str): The original question that was asked.
        answer (str): The generated answer from the LLM.
        context (KnwlContext): The context information including chunks, nodes, edges, and references.
        rag_time (float): Time taken for RAG operations in seconds.
        llm_time (float): Time taken for LLM processing in seconds.
        timestamp (str): ISO format timestamp of when the response was created.
    """
    # Note: Not frozen to allow mutation of timing fields during processing
    model_config = {"frozen": False}
    
    question: str = Field(default="None supplied", description="The original question that was asked.")
    answer: str = Field(default="None supplied", description="The generated answer from the LLM.")
    context: KnwlContext = Field(default_factory=KnwlContext, description="The context information including chunks, nodes, edges, and references.")
    
    rag_time: float = Field(default=0.0, description="Time taken for RAG operations in seconds.")
    llm_time: float = Field(default=0.0, description="Time taken for LLM processing in seconds.")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO format timestamp of when the response was created.")

    @property
    def total_time(self):
        return round(self.rag_time + self.llm_time, 2)

    def print(
        self,
        chunks: bool = True,
        nodes: bool = True,
        edges: bool = True,
        references: bool = True,
        metadata: bool = True,
    ):
        from knwl.format.terminal.terminal_formatter import print_response

        print_response(
            self,
            chunks=chunks,
            nodes=nodes,
            edges=edges,
            references=references,
            metadata=metadata,
        )

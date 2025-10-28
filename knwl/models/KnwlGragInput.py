from typing import Optional
from knwl.models.GragParams import GragParams
from knwl.models.KnwlInput import KnwlInput


from pydantic import Field, model_validator


class KnwlGragInput(KnwlInput):
    """
    Extends KnwlInput with additional fields for graph RAG (Retrieval-Augmented Generation) processing.
    """

    params: Optional[GragParams] = Field(
        default_factory=GragParams, description="Parameters for graph RAG processing."
    )

   
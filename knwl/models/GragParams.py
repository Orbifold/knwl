from typing import Literal

from pydantic import BaseModel, Field

QueryModes = Literal["local", "global", "hybrid", "naive"]


class GragParams(BaseModel):
    """
    Parameters of grag augmentation.
    
    Attributes:
        mode (QueryModes): The query mode to use - local, global, hybrid, or naive.
        
        response_type (str): The type of response format to generate.
        top_k (int): Number of top-k items to retrieve (entities in local mode, relationships in global mode).
        max_token_for_text_unit (int): Maximum number of tokens for original chunks.
        max_token_for_global_context (int): Maximum number of tokens for relationship descriptions.
        max_token_for_local_context (int): Maximum number of tokens for entity descriptions.
        return_context (bool): Whether to return the RAG context.
        return_references (bool): Whether to return the references.
    """
    model_config = {"frozen": True}

    mode: QueryModes = Field(default="global", description="The query mode to use - local, global, hybrid, or naive.")


    response_type: str = Field(default="Multiple Paragraphs", description="The type of response format to generate.")

    # Number of top-k items to retrieve; corresponds to entities in "local" mode and relationships in "global" mode.
    top_k: int = Field(default=60, description="Number of top-k items to retrieve (entities in local mode, relationships in global mode).")

    # Number of tokens for the original chunks.
    max_token_for_text_unit: int = Field(default=4000, description="Maximum number of tokens for original chunks.")

    # Number of tokens for the relationship descriptions
    max_token_for_global_context: int = Field(default=4000, description="Maximum number of tokens for relationship descriptions.")

    # Number of tokens for the entity descriptions
    max_token_for_local_context: int = Field(default=4000, description="Maximum number of tokens for entity descriptions.")

    # Whether to return the RAG context
    return_context: bool = Field(default=True, description="Whether to return the RAG context.")

    # Whether to return the references
    return_references: bool = Field(default=True, description="Whether to return the references.")

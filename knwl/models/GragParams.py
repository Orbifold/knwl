from typing import Literal

from pydantic import BaseModel, Field

QueryModes = Literal["local", "global", "hybrid", "naive", "keywords"]


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
        return_chunks (bool): Whether to return the chunks. If not, only the chunk Id's are returned and downstream services need to fetch the chunk data separately.
        return_references (bool): Whether to return the references.
    """
    model_config = {"frozen": True}

    mode: QueryModes = Field(default="local", description="The query mode to use - local, global, hybrid, or naive.")


    response_type: str = Field(default="Multiple Paragraphs", description="The type of response format to generate.")

    # Number of top-k items to retrieve; corresponds to entities in "local" mode and relationships in "global" mode.
    top_k: int = Field(default=5, description="Number of top-k items to retrieve (entities in local mode, relationships in global mode).")

    # Number of tokens for the original chunks.
    max_token_for_text_unit: int = Field(default=4000, description="Maximum number of tokens for original chunks.")

    # Number of tokens for the relationship descriptions
    max_token_for_global_context: int = Field(default=4000, description="Maximum number of tokens for relationship descriptions.")

    # Number of tokens for the entity descriptions
    max_token_for_local_context: int = Field(default=4000, description="Maximum number of tokens for entity descriptions.")

    # Whether to return the chunks
    return_chunks: bool = Field(default=False, description="Whether to return the chunks.")

    # Whether to return the references
    return_references: bool = Field(default=False, description="Whether to return the references of the sources.")

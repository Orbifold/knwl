from typing import Literal

from pydantic import BaseModel, Field

AugmentationStrategy = Literal["local", "global", "hybrid", "naive", "none", "self"]


class KnwlParams(BaseModel):
    """
    Parameters tuning graph RAG augmentation.

    Attributes:
        strategy (AugmentationStrategy): The query strategy to use - local, global, hybrid, self/none or naive.
        top_k (int): Number of top-k items to retrieve (entities in local mode, relationships in global mode).
        return_chunks (bool): Whether to return the chunks. If not, only the chunk Id's are returned and downstream services need to fetch the chunk data separately.
    """

    strategy: AugmentationStrategy = Field(
        default="local",
        description="The query strategy to use - local, global, hybrid, self or naive.",
    )

    top_k: int = Field(
        default=5,
        description="Number of top-k items to retrieve (entities in local mode, relationships in global mode).",
    )

    return_chunks: bool = Field(
        default=True,
        description="Whether to return the chunk text data or just the chunk Id's.",
    )

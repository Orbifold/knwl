from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Request model for asking questions or augmenting text."""

    question: str = Field(
        ..., description="The question or text to process", min_length=1
    )
    strategy: str | None = Field(
        None, description="Graph RAG strategy (local, global, hybrid, naive, self)"
    )
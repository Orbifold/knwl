from pydantic import BaseModel, Field


class CountResponse(BaseModel):
    """Response model for count endpoints."""

    count: int = Field(..., description="The count value")
from pydantic import BaseModel, Field


class NamespaceResponse(BaseModel):
    """Response model for namespace endpoint."""

    namespace: str = Field(..., description="The current namespace")
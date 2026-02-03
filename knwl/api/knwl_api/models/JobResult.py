from typing import Optional, Any
from pydantic import BaseModel, Field


class JobResult(BaseModel):
    job_type: str = Field(..., description="Type of the job")
    started_at: float = Field(..., description="Timestamp when job started")
    finished_at: float = Field(..., description="Timestamp when job finished")
    duration: float = Field(..., description="Duration in seconds")
    output: Optional[Any] = Field(None, description="Optional job-specific output payload")

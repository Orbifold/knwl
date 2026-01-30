from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    job_type:str = Field("Unknown", description="Type of the job")
    state: JobState = Field(description="Current state of the job")
    result: Optional[Any] = Field(default=None, description="Job result if completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: float = Field(0,description="Timestamp when job was created")
    finished_at: float = Field(0,description="Timestamp when job was done")


class JobResponse(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    message: str = Field(description="Response message")


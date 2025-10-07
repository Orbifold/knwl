from pydantic import BaseModel, Field


class JsonRequest(BaseModel):
    text: str = Field(..., description="The text to extract the graph from.")
    entities: list[str] | None = Field(None, description="The entities to extract.")
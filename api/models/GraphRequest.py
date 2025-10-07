from pydantic import BaseModel, Field


class GraphRequest(BaseModel):
    text: str = Field(..., description="The text to extract the graph from.")
    chunk_id: str | None = Field(None, description="The chunk Id to tag the extraction with.")
    entities: list[str] | None = Field(None, description="The entities to extract.")
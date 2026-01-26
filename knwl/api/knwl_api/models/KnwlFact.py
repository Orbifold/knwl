from typing import Optional

from pydantic import BaseModel, Field


class KnwlFact(BaseModel):
    id: Optional[str] = Field(default=None, description="Optional fact Id.")
    name: str = Field(description="Fact name.")
    content: str = Field(description="Fact content.")
    type: Optional[str] = Field(default="Fact", description="Optional fact type.")

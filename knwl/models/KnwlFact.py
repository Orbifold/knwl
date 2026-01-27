from typing import Optional

from pydantic import BaseModel, Field


class KnwlFact(BaseModel):
    """
    A fact is identical to a node in the knowledge graph, representing a discrete piece of information.
    It's being used by the Knwl utility and FastAPI endpoints to add facts to the knowledge graph.
    
    Attributes:
        id (Optional[str]): Optional fact Id.
        name (str): Fact name.
        content (str): Fact content.
        type (Optional[str]): Optional fact type.
    """
    id: Optional[str] = Field(default=None, description="Optional fact Id.")
    name: str = Field(description="Fact name.")
    content: str = Field(description="Fact content.")
    type: Optional[str] = Field(default="Fact", description="Optional fact type. This maps to the node type in the knowledge graph.")

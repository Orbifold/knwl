from knwl.models.KnwlInput import KnwlInput
from knwl.utils import hash_with_prefix
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime


class KnwlDocument(BaseModel):
    """
    A class representing a source document.

    Attributes:
        content (str): The content of the source document.
        id (str): A unique identifier for the source document. Defaults to a new UUID.
        timestamp (str): The timestamp when the source document was created. Defaults to the current time in ISO format.
        typeName (str): The type name of the source document. Defaults to "KnwlDocument".
        name (str): The name of the source document. Defaults to an empty string.
        description (str): A description of the source document. Defaults to an empty string.
    """

    content: str = Field(..., description="The content of the document")
    id: Optional[str] = Field(
        default=None, description="Unique identifier for the document"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Creation timestamp",
    )
    description: Optional[str] = Field(default="", description="Document description")
    name: Optional[str] = Field(default="", description="Document name")
    type_name: str = Field(
        default="KnwlDocument",
        frozen=True,
        description="The type name of this class, for serialization purposes.",
    )
    # todo: have ontology in a separate ontology store


    @field_validator("content")
    def content_not_empty(cls, v):
        if v is None or len(str.strip(v)) == 0:
            raise ValueError("Content of a KnwlDocument cannot be None or empty.")
        return v

    @model_validator(mode="after")
    def set_id(self) -> "KnwlDocument":
        if self.id is None and self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(
                self, "id", self.hash_keys(self.content, self.name, self.description)
            )
        return self

    @staticmethod
    def from_input(input: KnwlInput):
        return KnwlDocument(
            content=input.text, name=input.name, description=input.description, id=input.id
        )

    @staticmethod
    def hash_keys(content: str, name: str = None, description: str = None) -> str:
        return hash_with_prefix(
            content + " " + (name or "") + " " + (description or ""), prefix="doc|>"
        )

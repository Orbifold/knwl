from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.models.KnwlParams import KnwlParams
from knwl.utils import hash_with_prefix


class KnwlInput(BaseModel):

    text: str
    name: Optional[str] = Field(default_factory=lambda: f"Input {datetime.now().isoformat()}")
    description: Optional[str] = Field(
        default="", description="An optional description of the input text."
    )
    id: Optional[str] = Field(default=None)

    params: Optional[KnwlParams] = Field(
        default_factory=KnwlParams, description="Parameters for graph RAG processing."
    )
   
    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if v is None or len(str.strip(v)) == 0:
            raise ValueError("Content of a KnwlInput cannot be None or empty.")
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError("text must be a non-empty string.")
        return v

    @model_validator(mode="after")
    def set_id(self):
        if self.id is None:
            object.__setattr__(
                self, "id", KnwlInput.hash_keys(self.text, self.name, self.description)
            )
        return self

    @classmethod
    def from_text(
        cls, text: str, name: str = None, description: str = None
    ) -> "KnwlInput":
        """Create a KnwlInput from just text with optional name and description."""
        return cls(
            text=text,
            name=name or f"Input {datetime.now().isoformat()}",
            description=description or "",
        )

    @staticmethod
    def hash_keys(text: str, name: str = None, description: str = None) -> str:
        return hash_with_prefix(
            text + " " + (name or "") + " " + (description or ""), prefix="in-"
        )



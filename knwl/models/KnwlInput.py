from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlInput(BaseModel):

    text: str
    name: str = Field(default_factory=lambda: f"Input {datetime.now().isoformat()}")
    description: str = Field(
        default="", description="An optional description of the input text."
    )
    id: Optional[str] = Field(default=None)

    model_config = {"frozen": True}

    def __init__(self, text=None, name=None, description=None, id=None, **kwargs):
        """Allow KnwlInput('text') syntax or keyword arguments."""
        if (
            isinstance(text, str)
            and name is None
            and description is None
            and id is None
        ):
            # Handle KnwlInput("text") case
            super().__init__(
                text=text,
                name=f"Input {datetime.now().isoformat()}",
                description="",
                id=None,
                **kwargs,
            )
        else:
            # Handle normal keyword arguments
            super().__init__(
                text=text,
                name=name or f"Input {datetime.now().isoformat()}",
                description=description or "",
                id=id,
                **kwargs,
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



from typing import Optional
from knwl.models.KnwlInput import KnwlInput


from pydantic import Field, model_validator


class KnwlRagInput(KnwlInput):
    """
    Extends KnwlInput with additional fields for graph RAG (Retrieval-Augmented Generation) processing.
    """
    mode: Optional[str] = Field(
        default="hybrid", description="Sets the mode for KG context retrieval."
    )

    @model_validator(mode="after")
    def set_id(self):
        if self.id is None:
            object.__setattr__(
                self,
                "id",
                KnwlInput.hash_keys(
                    self.text, self.name, self.description, self.source or ""
                ),
            )
        return self
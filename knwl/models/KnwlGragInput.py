from typing import Optional
from knwl.models.GragParams import GragParams
from knwl.models.KnwlInput import KnwlInput


from pydantic import Field, model_validator


class KnwlGragInput(KnwlInput):
    """
    Extends KnwlInput with additional fields for graph RAG (Retrieval-Augmented Generation) processing.
    """

    params: GragParams = Field(
        default_factory=GragParams, description="Parameters for graph RAG processing."
    )

    # @model_validator(mode="after")
    # def set_id(self):
    #     if self.id is None:
    #         object.__setattr__(
    #             self,
    #             "id",
    #             KnwlInput.hash_keys(
    #                 self.text, self.name, self.description, self.params.mode or ""
    #             ),
    #         )
    #     return self

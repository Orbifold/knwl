from typing import Optional
from pydantic import BaseModel, Field


class KnwlText(BaseModel):
    """
    Represents a piece of text obtained via one of the Grag strategies.

    Attributes:
        origin_id (str): The source id of the text.
        text (str): The actual text content.
        order (int): The order of the text in the sequence.
        id (str): The unique identifier of the text.
    """

    origin_id: Optional[str] = Field(
        default=None, description="The source id of the text."
    )
    text: Optional[str] = Field(
        default="",
        description="The text content to use for context. If not supplied, downstream services need to fetch the text data separately using the id.",
    )
    index: Optional[int] = Field(
        default=0, description="The order of the text in the sequence."
    )
    id: Optional[str] = Field(
        default=None, description="The unique identifier of the text."
    )

    @staticmethod
    def get_header():
        return ["id", "content"]

    def to_row(self):
        return "\t".join([self.origin_id or "", self.text])
 
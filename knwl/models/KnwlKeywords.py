from pydantic import BaseModel


class KnwlKeywords(BaseModel):
    low_level: list[str]
    high_level: list[str]

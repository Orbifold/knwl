from dataclasses import dataclass


@dataclass(frozen=True)
class KnwlRagText:
    index: str
    text: str
    order: int
    id: str
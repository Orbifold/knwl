from dataclasses import dataclass


@dataclass(frozen=True)
class KnwlRagReference:
    index: str
    name: str
    description: str
    timestamp: str
    id: str
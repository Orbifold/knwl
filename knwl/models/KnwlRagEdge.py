from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class KnwlRagEdge:
    index: str
    id: str
    source: str
    target: str
    description: str
    keywords: List[str]
    weight: float
    order: int

    @staticmethod
    def get_header():
        return ["id", "source", "target", "description", "keywords", "weight"]

    def to_row(self):
        return "\t".join(
            [self.index, self.source, self.target, self.description, ", ".join(self.keywords), str(self.weight)]
        )
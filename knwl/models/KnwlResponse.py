from dataclasses import dataclass, field
from datetime import datetime

from knwl.models.KnwlContext import KnwlContext


@dataclass(frozen=False)
class KnwlResponse:
    answer: str = field(default="None supplied")
    context: KnwlContext = field(default_factory=KnwlContext)

    rag_time: float = field(default=0.0)
    llm_time: float = field(default=0.0)
    timestamp: str = field(default=datetime.now().isoformat())

    @property
    def total_time(self):
        return round(self.rag_time + self.llm_time, 2)

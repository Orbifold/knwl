from knwl.models.KnwlContext import KnwlContext


from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class KnwlResponse:
    answer: str = field(default="None supplied")
    context: KnwlContext = field(default_factory=KnwlContext)
    timing: float = field(default=0.0)
    timestamp: str = field(default=datetime.now().isoformat())
from dataclasses import dataclass, field
from datetime import datetime

from rich.text import Text

from knwl.models.KnwlContext import KnwlContext


@dataclass(frozen=False)
class KnwlResponse:
    question: str = field(default="None supplied")
    answer: str = field(default="None supplied")
    context: KnwlContext = field(default_factory=KnwlContext)

    rag_time: float = field(default=0.0)
    llm_time: float = field(default=0.0)
    timestamp: str = field(default=datetime.now().isoformat())

    @property
    def total_time(self):
        return round(self.rag_time + self.llm_time, 2)

    def print(
        self,
        chunks: bool = True,
        nodes: bool = True,
        edges: bool = True,
        references: bool = True,
        metadata: bool = True,
    ):
        from knwl.format.terminal.terminal_formatter import print_response

        print_response(
            self,
            chunks=chunks,
            nodes=nodes,
            edges=edges,
            references=references,
            metadata=metadata,
        )

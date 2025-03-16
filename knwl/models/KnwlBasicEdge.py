from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class KnwlBasicEdge:
    sourceId: str
    targetId: str
    id: str = field(default=str(uuid4()))
    description: str = field(default="")
    typeName: str = "KnwlBasicEdge"
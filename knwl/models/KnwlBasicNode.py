from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class KnwlBasicNode:
    id: str = field(default=str(uuid4()))
    name: str = field(default="")
    type: str = field(default="UNKNOWN")
    description: str = field(default="")
    typeName: str = "KnwlBasicNode"
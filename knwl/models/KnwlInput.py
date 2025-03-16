from dataclasses import dataclass, field
from datetime import datetime

from knwl.utils import hash_with_prefix


@dataclass(frozen=True)
class KnwlInput:
    text: str
    name: str = field(default_factory=lambda: f"Document {datetime.now().isoformat()}")
    description: str = field(default="")
    id: str = field(default=None)

    def __post_init__(self):
        if self.text is None or len(str.strip(self.text)) == 0:
            raise ValueError("Content of a KnwlInput cannot be None or empty.")
        if self.id is None:
            object.__setattr__(self, "id", KnwlInput.hash_keys(self.text, self.name, self.description))

    @staticmethod
    def hash_keys(text: str, name: str = None, description: str = None) -> str:
        return hash_with_prefix(text + " " + (name or "") + " " + (description or ""), prefix="in-")

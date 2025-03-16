from knwl.models.KnwlInput import KnwlInput
from knwl.utils import hash_with_prefix


from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class KnwlDocument:
    """
    A (immutable) class representing a source document.

    Attributes:
        content (str): The content of the source document.
        id (str): A unique identifier for the source document. Defaults to a new UUID.
        timestamp (str): The timestamp when the source document was created. Defaults to the current time in ISO format.
        typeName (str): The type name of the source document. Defaults to "KnwlDocument".
        name (str): The name of the source document. Defaults to an empty string.
        description (str): A description of the source document. Defaults to an empty string.
    """

    content: str
    id: str = field(default=None)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = field(default="")
    name: str = field(default="")
    typeName: str = "KnwlDocument"

    @staticmethod
    def from_input(input: KnwlInput):
        return KnwlDocument(content=input.text, name=input.name, description=input.description)

    def update_id(self):
        if self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(self, "id", self.hash_keys(self.content, self.name, self.description))
        else:
            object.__setattr__(self, "id", None)

    def __post_init__(self):
        if self.content is None or len(str.strip(self.content)) == 0:
            raise ValueError("Content of a KnwlDocument cannot be None or empty.")
        self.update_id()

    @staticmethod
    def hash_keys(content: str, name: str = None, description: str = None) -> str:
        return hash_with_prefix(content + " " + (name or "") + " " + (description or ""), prefix="doc-")
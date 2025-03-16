from knwl.utils import hash_with_prefix


from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnwlChunk:
    tokens: int
    content: str
    originId: str = field(default=None)
    index: int = field(default=0)
    typeName: str = "KnwlChunk"
    id: str = field(default=None)

    @staticmethod
    def hash_keys(content: str) -> str:
        return hash_with_prefix(content, prefix="chunk-")

    def update_id(self):
        if self.content is not None and len(str.strip(self.content)) > 0:
            object.__setattr__(self, "id", KnwlChunk.hash_keys(self.content))
        else:
            object.__setattr__(self, "id", None)

    def __post_init__(self):
        if self.content is None or len(str.strip(self.content)) == 0:
            raise ValueError("Content of a KnwlChunk cannot be None or empty.")
        self.update_id()

    @staticmethod
    def from_text(text: str):
        from ..tokenize import count_tokens
        return KnwlChunk(tokens=count_tokens(text), content=text)
from dataclasses import dataclass, field
from typing import List

from knwl.utils import hash_with_prefix


@dataclass(frozen=False)
class KnwlLLMAnswer:
    messages: List[dict] = field(default_factory=list)
    llm_model: str = field(default="qwen2.5:14b")
    llm_service: str = field(default="ollama")
    answer: str = field(default="")
    timing: float = field(default=0.0)
    category: str = field(default="")
    input:str = field(default="")

    from_cache: bool = field(default=False)
    id: str = field(default=None)

    def __post_init__(self):
        if self.id is None:
            object.__setattr__(self, "id", KnwlLLMAnswer.hash_keys(self.messages, self.llm_service, self.llm_model))

    @staticmethod
    def hash_keys(messages: List[dict], llm_service: str, llm_model: str) -> str:
        return hash_with_prefix(str(messages) + llm_service + llm_model, prefix="llm-")

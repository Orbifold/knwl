from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlLLMAnswer(BaseModel):
    messages: List[dict] = Field(default_factory=list)
    llm_model: str = Field(default="qwen2.5:14b")
    llm_service: str = Field(default="ollama")
    answer: str = Field(default="")
    timing: float = Field(default=0.0)
    key: str = Field(default="")
    category: str = Field(default="")
    question: str = Field(default="")
    from_cache: bool = Field(default=False)
    id: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def set_id_if_none(self):
        if self.id is None:
            self.id = KnwlLLMAnswer.hash_keys(
                self.messages, self.llm_service, self.llm_model
            )
        return self

    @staticmethod
    def hash_keys(messages: List[dict], llm_service: str, llm_model: str) -> str:
        return hash_with_prefix(str(messages) + llm_service + llm_model, prefix="answer|>")

    def __repr__(self):
        return f"<KnwlLLMAnswer, service={self.llm_service}, model={self.llm_model}, timing={self.timing}, from_cache={self.from_cache}>"

    def __str__(self):
        return self.__repr__()

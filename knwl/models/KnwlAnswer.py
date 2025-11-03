from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from knwl.utils import hash_with_prefix


class KnwlAnswer(BaseModel):
    """
    A Pydantic model representing an LLM (Large Language Model) answer with caching capabilities.

    This class encapsulates the response from a LLM along with metadata about
    the query, timing information, and caching status. It automatically generates a unique
    ID based on the messages, service, and model used.

    Attributes:
        messages (list[dict]): The conversation messages exchanged with the LLM.
        llm_model (str): The specific LLM model used (default: "qwen2.5:14b").
        llm_service (str): The LLM service provider (default: "ollama").
        answer (str): The generated response from the LLM.
        timing (float): The time taken to generate the answer in seconds.
        key (str): An optional key for categorizing or identifying the answer.
        category (str): The category or classification of the answer.
        question (str): The original question or prompt that generated this answer.
        from_cache (bool): Indicates whether the answer was retrieved from cache.
        id (Optional[str]): Unique identifier for the answer, auto-generated if not provided.
  
    Example:
        ```python
        llm = services.get_service("llm")
        a = await llm.ask("DNA is the essence of life.")
        print_knwl(a)
        ```
                
╭─────────────────────────────── KnwlLLMAnswer ────────────────────────────────╮
│                                                                              │
│   messages      [1 items]                                                    │
│   llm_model     o14                                                          │
│   llm_service   ollama                                                       │
│   answer        While DNA plays an incredibly important role in biology      │
│                 and genetics, it's more accurate to say that DNA is          │
│                 essential for storing genetic informati...                   │
│   timing        12.5                                                         │
│   key           DNA is the essence of life.                                  │
│   category      none                                                         │
│   question      DNA is the essence of life.                                  │
│   from_cache    True                                                         │
│   id            answer|>6f80fc51a926b69400c1cb5f982074ae                     │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

    """
    messages: list[dict] = Field(default_factory=list)
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
            self.id = KnwlAnswer.hash_keys(
                self.messages, self.llm_service, self.llm_model
            )
        return self

    @staticmethod
    def none() -> "KnwlAnswer":
        return KnwlAnswer(
            answer="I don't know.",
            messages=[],
            llm_model="",
            llm_service="",
            timing=0.0,
            key="",
            category="",
            question="",
            from_cache=False,
        )
    @staticmethod
    def hash_keys(messages: list[dict], llm_service: str, llm_model: str) -> str:
        return hash_with_prefix(str(messages) + llm_service + llm_model, prefix="answer|>")

    def __repr__(self):
        return f"<KnwlLLMAnswer, service={self.llm_service}, model={self.llm_model}, timing={self.timing}, from_cache={self.from_cache}>"

    def __str__(self):
        return self.__repr__()

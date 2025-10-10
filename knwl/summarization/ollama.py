from knwl.prompts import prompts
from knwl.summarization.summarization_base import SummarizationBase


class OllamaSummarization(SummarizationBase):
    """
    Summarization using the Ollama LLM service.

    The token length depends typically on the object considered:
        - entities: 200 tokens
        - concepts: 150 tokens
        - relationships: 100 tokens
        - document: 300 tokens

    args:
        model (str): The name of the Ollama model to use for summarization. Default is "gemma3:4b".
        service (str): The service to use for Ollama. Default is "ollama".
        max_tokens (int): The maximum number of tokens to use for the summary. Default is 150.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self.model = self.get_param(["summarization", "ollama", "model"], args, kwargs, default="gemma3:4b", override=config, )
        self.max_tokens = self.get_param(["summarization", "ollama", "max_tokens"], args, kwargs, default=150, override=config, )
        self.chunker_name = self.get_param(["summarization", "ollama", "chunker"], args, kwargs, default="tiktoken", override=config, )
        self.chunker = self.get_service("chunking", self.chunker_name, override=config)
        if self.chunker is None:
            raise ValueError(f"Chunker '{self.chunker_name}' not found in configuration.")
        self.llm = self.get_service("llm", "ollama", override=config)
        if self.llm is None:
            raise ValueError("Ollama LLM service not found in configuration.")

    async def summarize(self, content: str | list[str], entity_or_relation_name: str | list[str] = None) -> str:
        if isinstance(content, list):
            content = " ".join(content)
        tokens = self.chunker.encode(content)

        if len(tokens) <= self.max_tokens:
            return content

        description = self.chunker.decode(tokens[: self.max_tokens])

        use_prompt = prompts.summarization.summarize(description) if entity_or_relation_name is None else prompts.summarization.summarize_entity(description, entity_or_relation_name)
        resp = await self.llm.ask(use_prompt)
        return resp.answer

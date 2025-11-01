from knwl.chunking.chunking_base import ChunkingBase
from knwl.di import defaults
from knwl.llm.llm_base import LLMBase
from knwl.prompts import prompts
from knwl.summarization.summarization_base import SummarizationBase

@defaults("summarization")
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

    def __init__(
        self, llm: LLMBase = None, chunker: ChunkingBase = None, max_tokens: int = 150
    ):
        super().__init__()
        self.chunker = chunker
        self.llm = llm
        self.max_tokens = max_tokens
        if llm is None:
            raise ValueError("OllamaSummarization: LLM instance must be provided.")
        if not isinstance(llm, LLMBase):
            raise TypeError(
                "OllamaSummarization: llm parameter must be an instance of LLMBase."
            )
        if chunker is None:
            raise ValueError("OllamaSummarization: Chunker instance must be provided.")
        if not isinstance(chunker, ChunkingBase):
            raise TypeError(
                "OllamaSummarization: chunker parameter must be an instance of ChunkingBase."
            )

    async def summarize(
        self, content: str | list[str], entity_or_relation_name: str | list[str] = None
    ) -> str:
        if isinstance(content, list):
            content = " ".join(content)
        tokens = await self.chunker.encode(content)

        if len(tokens) <= self.max_tokens:
            return content

        description = await self.chunker.decode(tokens[: self.max_tokens])

        use_prompt = (
            prompts.summarization.summarize(description)
            if entity_or_relation_name is None
            else prompts.summarization.summarize_entity(
                description, entity_or_relation_name
            )
        )
        resp = await self.llm.ask(use_prompt)
        return resp.answer

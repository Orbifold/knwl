from knwl.di import defaults
from knwl.summarization.summarization_base import SummarizationBase

@defaults("summarization", "concat")
class SimpleConcatenation(SummarizationBase):
    """
    Fake summarization that concatenates the input content.
    This doesn't do any real summarization, but is useful for testing.

    args:
        length (int): The maximum length of the concatenated content. If the content exceeds this length,
                      it will be truncated and "..." will be appended. If None, no truncation is done.
                      Default is 500.
    """

    def __init__(self,max_tokens: int = 500):
        super().__init__()
        self.max_tokens = max_tokens


    async def summarize(self, content: str | list[str], entity_or_relation_name: str|list[str] = None) -> str:
        if isinstance(content, list):
            content = "\n".join(content)
        if self.max_tokens is not None and len(content) > self.max_tokens:
            return content[: self.max_tokens] + "..."
        return content

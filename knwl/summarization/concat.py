from knwl.summarization.summarization_base import SummarizationBase


class SimpleConcatenation(SummarizationBase):
    """
    Fake summarization that concatenates the input content.
    This doesn't do any real summarization, but is useful for testing.

    args:
        length (int): The maximum length of the concatenated content. If the content exceeds this length,
                      it will be truncated and "..." will be appended. If None, no truncation is done.
                      Default is 500.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self.max_tokens = self.get_param(
            ["summarization", "concat", "max_tokens"],
            args,
            kwargs,
            default=500,
            override=config,
        )

    async def summarize(self, content: str | list[str], entity_or_relation_name: str|list[str] = None) -> str:
        if isinstance(content, list):
            content = "\n".join(content)
        if self.length is not None and len(content) > self.length:
            return content[: self.length] + "..."
        return content

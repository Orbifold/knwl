from knwl.summarization.summarization_base import SummarizationBase


class DefaultSummarization(SummarizationBase):
    async def summarize(self, content: str | list[str]) -> str:
        if isinstance(content, list):
            content = "\n".join(content)

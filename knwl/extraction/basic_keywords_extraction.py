from knwl.di import defaults
from knwl.extraction.keywords_extraction_base import KeywordsExtractionBase
from knwl.llm.llm_base import LLMBase
from knwl.models import KnwlKeywords
from knwl.prompts import prompts
from knwl.utils import hash_with_prefix
import json
from knwl.logging import log


@defaults("keywords_extraction")
class BasicKeywordsExtraction(KeywordsExtractionBase):
    """
    Basic implementation of KeywordsExtractionBase that extracts keywords using simple splitting.

    Methods:
        extract: Extracts keywords from text by splitting on whitespace and punctuation.

    Note:
        This is a basic implementation and may not handle complex keyword extraction scenarios.
    """

    def __init__(self, llm: LLMBase=None):
        super().__init__()
        self.llm = llm
        if not self.llm:
            raise ValueError(
                "BasicKeywordsExtraction: LLM instance is required for extraction."
            )
        if not isinstance(self.llm, LLMBase):
            raise TypeError(
                "BasicKeywordsExtraction: llm must be an instance of LLMBase."
            )

    async def extract(self, text: str, chunk_id: str = None) -> KnwlKeywords | None:
        prompt = prompts.extraction.keywords_extraction(text=text)
        result = await self.llm.ask(prompt)

        try:
            keywords_data = json.loads(result.answer)
            low_keywords = keywords_data.get("low_level_keywords", [])
            high_keywords = keywords_data.get("high_level_keywords", [])
            return KnwlKeywords(
                low_level=low_keywords,
                high_level=high_keywords,
            )
        except json.JSONDecodeError:

            log.warning(
                "BasicKeywordsExtraction: Failed to parse keywords extraction result as JSON."
            )
            return None

import os.path

from knwl.prompts.prompt_constants import PromptConstants
from knwl.prompts.extraction_prompts import ExtractionPrompts
from knwl.prompts.rag_prompts import RagPrompts
from knwl.prompts.summarization_prompts import SummarizationPrompts


class Prompts:
    """
    A centralized manager for accessing various types of prompt templates.

    This class provides organized access to different categories of prompts used throughout
    the application, including extraction, summarization, RAG (Retrieval-Augmented Generation),
    and constant prompts.

    Attributes:
        extraction (ExtractionPrompts): Prompts related to information extraction tasks.
        constants (PromptConstants): Constant prompt values and templates.
        summarization (SummarizationPrompts): Prompts for text summarization operations.
        rag (RagPrompts): Prompts for retrieval-augmented generation workflows.

    Example:
        >>> prompts = Prompts()
        >>> extraction_prompt = prompts.extraction
        >>> summary_prompt = prompts.summarization
    """
    def __init__(self):
        self._constants = PromptConstants()
        self._summarization = SummarizationPrompts()
        self._extraction = ExtractionPrompts()
        self._rag = RagPrompts()

    @property
    def extraction(self) -> ExtractionPrompts:
        return self._extraction

    @property
    def constants(self) -> PromptConstants:
        return self._constants

    @property
    def summarization(self) -> SummarizationPrompts:
        return self._summarization

    @property
    def rag(self) -> RagPrompts:
        return self._rag


prompts = Prompts()

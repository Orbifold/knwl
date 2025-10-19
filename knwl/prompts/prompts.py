import os.path

from knwl.prompts.prompt_constants import PromptConstants
from knwl.prompts.extraction_prompts import ExtractionPrompts
from knwl.prompts.summarization_prompts import SummarizationPrompts



class Prompts:
    def __init__(self):
        self._constants = PromptConstants()
        self._summarization = SummarizationPrompts()
        self._extraction = (
            ExtractionPrompts()
        )   

    @property
    def extraction(self) -> ExtractionPrompts:
        return self._extraction

    @property
    def constants(self) -> PromptConstants:
        return self._constants

    @property
    def summarization(self) -> SummarizationPrompts:
        return self._summarization


prompts = Prompts()

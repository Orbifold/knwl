from typing import List

from knwl.logging import log
from knwl.models import (
    KnwlChunk,
    KnwlContext,
    KnwlText,
)
from knwl.models.KnwlInput import KnwlInput
from knwl.semantic.graph_rag.graph_rag_base import GraphRAGBase
from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase
from knwl.prompts.prompts import prompts
from knwl.services import services
from knwl.utils import answer_to_records, split_string_by_multi_markers


class SelfGragStrategy(GragStrategyBase):
    """
    This strategy does not use any graph-based augmentation.
    It asks the LLM to generate its own context based on the input question.
    """

    def __init__(self, grag: GraphRAGBase):
        super().__init__(grag)

    async def augment(self, input: KnwlInput) -> KnwlContext | None:
        prompt = prompts.rag.self_rag(input.text)
        llm = services.get_service("llm")
        answ = await llm.ask(prompt)
        if answ is None or not answ.answer or answ.answer.strip() == "":
            return KnwlContext.empty(input)
        parts = split_string_by_multi_markers(
            answ.answer,
            [
                prompts.constants.DEFAULT_RECORD_DELIMITER,
                prompts.constants.DEFAULT_COMPLETION_DELIMITER,
            ],
        )

        chunks = [KnwlChunk(content=part, source="self_strategy") for part in parts if part.strip() != ""]
        if not chunks:
            return KnwlContext.empty(input)
        if input.params.return_chunks:
            texts = await self.texts_from_chunks(chunks, params=input.params)
            references = [] # Self strategy does not provide references
        else:
            texts = []
            references = []
        return KnwlContext(
            input=input,
            texts=texts,
            nodes=[],
            edges=[],
            references=references,
        )

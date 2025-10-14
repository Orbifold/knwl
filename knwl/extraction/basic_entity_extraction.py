from knwl.extraction.entity_extraction_base import EntityExtractionBase
from knwl.prompts import prompts
from knwl.utils import parse_llm_record, split_string_by_multi_markers
from knwl.llm.llm_base import LLMBase
from knwl.di import service


@service("llm")
class BasicEntityExtraction(EntityExtractionBase):
    """
    A basic entity extraction which in essence asks an LLM to extract named entities from text.

    Args:
        llm (LLMBase): The LLM instance to use for entity extraction. Must be provided and
                       must be an instance of LLMBase. Make sure the LLM has at least 14b params since the smaller models struggle or even hang.

    """

    def __init__(self, llm: LLMBase = None):
        super().__init__()

        if llm is None:
            raise ValueError("BasicEntityExtraction: LLM instance must be provided.")
        if not isinstance(llm, LLMBase):
            raise TypeError(
                "BasicEntityExtraction: llm must be an instance of LLMBase."
            )
        self._llm = llm

    @property
    def llm(self):
        """
        Get the llm instance used for entity extraction.

        Returns:
            The configured llm instance used for entity extraction.
        """
        return self._llm

    def get_extraction_prompt(self, text, entity_types=None):
        return prompts.extraction.fast_entity_extraction(text, entity_types)

    def answer_to_records(self, answer: str) -> list[list] | None:
        if not answer or answer.strip() == "":
            return None
        parts = split_string_by_multi_markers(
            answer,
            [
                prompts.constants.DEFAULT_RECORD_DELIMITER,
                prompts.constants.DEFAULT_COMPLETION_DELIMITER,
            ],
        )
        coll = []
        for part in parts:
            coll.append(
                parse_llm_record(part, prompts.constants.DEFAULT_TUPLE_DELIMITER)
            )
        return coll

    async def extract(
        self, text: str, entities: list[str] = None, chunk_id: str = None
    ) -> dict | None:
        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(text, entity_types=entities)
        found = await self._llm.ask(
            question=extraction_prompt, key=text, category="entity-extraction"
        )
        if not found or found.answer.strip() == "":
            return None
        return self.answer_to_records(found.answer)

    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(text, entity_types=entities)
        found = await self._llm.ask(
            question=extraction_prompt, key=text, category="entity-extraction"
        )
        if not found or found.answer.strip() == "":
            return None
        return self.answer_to_records(found.answer)

    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        records = await self.extract_records(text, entities=entities)
        if not records:
            return None
        result = {}
        for record in records:
            if len(record) < 3:
                continue
            name = record[0]
            type_ = record[1].lower().strip("<>")
            description = record[2].strip("\\")
            if type_ not in result:
                result[type_] = []
            result[type_].append({"name": name, "description": description})
        return result

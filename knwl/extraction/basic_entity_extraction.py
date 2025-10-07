from knwl.extraction.entity_extraction_base import EntityExtractionBase
from knwl.prompts import prompts
from knwl.utils import parse_llm_record, split_string_by_multi_markers


class BasicEntityExtraction(EntityExtractionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        llm_variant = self.get_param(["entity_extraction", "basic", "llm"], args, kwargs, default="ollama", override=config, )

        self.llm = self.get_llm(llm_variant, override=config)

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
        found = await self.llm.ask(
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
        found = await self.llm.ask(
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
            type_ = record[1].lower().strip('<>')
            description = record[2].strip('\\')
            if type_ not in result:
                result[type_] = []
            result[type_].append({"name": name, "description": description})
        return result

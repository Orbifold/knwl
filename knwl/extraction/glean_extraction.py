from knwl.extraction.extraction_base import ExtractionBase
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.prompts import prompts
from knwl.utils import parse_llm_record, split_string_by_multi_markers

continue_prompt = prompts.extraction.iterate_entity_extraction
if_loop_prompt = prompts.extraction.glean_break


class GleaningExtraction(ExtractionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        llm_variant = self.get_param(
            ["extraction", "glean", "llm"],
            args,
            kwargs,
            default="ollama",
            override=config,
        )

        self.llm = self.get_llm(llm_variant, override=config)

    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        if not text or text.strip() == "":
            return None
        extraction_prompt = prompts.extraction.full_entity_extraction(
            text, entity_types=entities
        )
        found = await self.llm.ask(
            question=extraction_prompt, key=text, category="extraction"
        )
        if not found or found.answer.strip() == "":
            return None
        parts = split_string_by_multi_markers(
            found.answer,
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

    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        records = await self.extract_records(text, entities)
        if not records:
            return None
        return self.records_to_json(records)

    async def extract(self, text: str, entities: list[str] = None) -> KnwlExtraction | None:
        records = await self.extract_records(text,entities)
        if not records:
            return None
        return self.records_to_extraction(records)

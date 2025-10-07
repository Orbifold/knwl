from knwl.extraction.graph_extraction_base import GraphExtractionBase
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlGraph import KnwlGraph
from knwl.prompts import prompts
from knwl.utils import parse_llm_record, split_string_by_multi_markers

continue_prompt = prompts.extraction.iterate_entity_extraction
if_loop_prompt = prompts.extraction.glean_break


class BasicGraphExtraction(GraphExtractionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        llm_variant = self.get_param(["graph_extraction", "basic", "llm"], args, kwargs, default="ollama", override=config, )
        self.llm = self.get_llm(llm_variant, override=config)

    def get_extraction_prompt(self, text, entity_types=None):
        if self.extraction_mode == "fast":
            return prompts.extraction.fast_graph_extraction(text, entity_types)
        if self.extraction_mode == "full":
            return prompts.extraction.full_graph_extraction(text, entity_types)
        else:
            raise ValueError(f"Unknown extraction mode: {self.extraction_mode}")

    async def extract_records(self, text: str, entities: list[str] = None) -> list[list] | None:
        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(text, entity_types=entities)
        found = await self.llm.ask(question=extraction_prompt, key=text, category="graph-extraction")
        if not found or found.answer.strip() == "":
            return None
        return self.answer_to_records(found.answer)

    async def extract_json(self, text: str, entities: list[str] = None) -> dict | None:
        records = await self.extract_records(text, entities)
        if not records:
            return None
        return GraphExtractionBase.records_to_json(records)

    async def extract(self, text: str, entities: list[str] = None, chunk_id: str = None) -> KnwlExtraction | None:
        records = await self.extract_records(text, entities)
        if not records:
            return None
        return GraphExtractionBase.records_to_extraction(records, chunk_id)

    async def extract_graph(self, text: str, entities: list[str] = None, chunk_id: str = None) -> KnwlGraph | None:
        extraction = await self.extract(text, entities, chunk_id=chunk_id)
        if not extraction:
            return None
        return GraphExtractionBase.extraction_to_graph(extraction)

    def answer_to_records(self, answer: str) -> list[list] | None:
        if not answer or answer.strip() == "":
            return None
        parts = split_string_by_multi_markers(answer, [prompts.constants.DEFAULT_RECORD_DELIMITER, prompts.constants.DEFAULT_COMPLETION_DELIMITER, ], )
        coll = []
        for part in parts:
            coll.append(parse_llm_record(part, prompts.constants.DEFAULT_TUPLE_DELIMITER))
        return coll

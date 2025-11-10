from knwl.di import defaults
from knwl.extraction.graph_extraction_base import GraphExtractionBase
from knwl.llm.llm_base import LLMBase
from knwl.logging import log
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlGraph import KnwlGraph
from knwl.prompts import prompts
from knwl.utils import answer_to_records

continue_prompt = prompts.extraction.iterate_entity_extraction
if_loop_prompt = prompts.extraction.glean_break


@defaults("graph_extraction")
class BasicGraphExtraction(GraphExtractionBase):
    def __init__(self, llm: LLMBase = None, mode: str = "full"):
        super().__init__()
        if llm is None:
            raise ValueError("BasicGraphExtraction: LLM instance must be provided.")
        if not isinstance(llm, LLMBase):
            raise TypeError("BasicGraphExtraction: llm must be an instance of LLMBase.")
        self._llm = llm
        self.extraction_mode = mode

    @property
    def llm(self) -> LLMBase:
        return self._llm

    

    async def extract_records(self, text: str, entities: list[str] = None) -> list[list] | None:
        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(text, entity_types=entities)
        found = await self.llm.ask(question=extraction_prompt, key=text, category="graph-extraction")
        if not found or found.answer.strip() == "":
            return None
        return answer_to_records(found.answer)

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

    
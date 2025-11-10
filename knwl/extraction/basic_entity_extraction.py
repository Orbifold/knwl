from knwl.extraction.entity_extraction_base import EntityExtractionBase
from knwl.prompts import prompts
from knwl.utils import answer_to_records
from knwl.llm.llm_base import LLMBase
from knwl.di import defaults
from knwl.models import KnwlEntity


@defaults("entity_extraction")
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
                "BasicEntityExtraction: llm parameter must be an instance of LLMBase."
            )
        print(f"Using LLM {llm} for entity extraction.")
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

    

    async def extract(
        self, text: str, entities: list[str] = None, chunk_id: str = None
    ) -> list[KnwlEntity] | None:
        """
        Extracts named entities from the given text using an LLM.

        This method processes the input text to identify and extract entities of specified types.
        It uses a language model to perform the extraction and returns structured entity objects.

        Args:
            text (str): The text to extract entities from. Must be non-empty.
            entities (list[str], optional): List of specific entity types to extract.
                If None, extracts all available entity types.
            chunk_id (str, optional): Identifier for the text chunk being processed.
                Used for tracking and referencing purposes.

        Returns:
            list[KnwlEntity] | None: A list of extracted entities as KnwlEntity objects,
                or None if no text provided, no entities found, or extraction failed.
                Each entity contains name, type, description, and optional chunk_id.

        Raises:
            Any exceptions from the underlying LLM service or answer parsing.
        """
        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(text, entity_types=entities)
        found = await self._llm.ask(
            question=extraction_prompt, key=text, category="entity-extraction"
        )
        if not found or found.answer.strip() == "":
            return None
        recs = answer_to_records(found.answer)
        if not recs:
            return None
        result = []
        for record in recs:
            if len(record) < 3:
                continue
            # first is 
            name = record[0]
            type_ = record[1].lower()
            description = record[2]
            entity = KnwlEntity(
                entity=name,
                type=type_,
                description=description,
                chunk_id=chunk_id,
            )
            result.append(entity)
        return result

    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        """
        Extracts named entities from the given text and returns them as a list of records.
        Each record is a list containing the entity name, type, and description.
        """
        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(text, entity_types=entities)
        found = await self._llm.ask(
            question=extraction_prompt, key=text, category="entity-extraction"
        )
        if not found or found.answer.strip() == "":
            return None
        return answer_to_records(found.answer)

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

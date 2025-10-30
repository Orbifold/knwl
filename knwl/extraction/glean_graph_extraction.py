from knwl.prompts import prompts
from knwl.extraction.basic_graph_extraction import BasicGraphExtraction
from knwl.logging import log
from knwl.llm.llm_base import LLMBase
from knwl.di import defaults
from knwl.utils import answer_to_records

@defaults("glean_graph_extraction")
class GleanGraphExtraction(BasicGraphExtraction):
    """
    An advanced extraction class that iteratively refines entity extraction through multiple gleaning passes.

    This class extends BasicExtraction to perform iterative entity extraction, where after the initial
    extraction, it performs additional "gleaning" passes to find entities that may have been missed
    in the first attempt. The process continues until no new entities are found or the maximum
    number of gleaning iterations is reached.

    Attributes:
        max_glean (int): Maximum number of gleaning iterations to perform. Defaults to 3.
                        If set to 1 or less, falls back to basic extraction behavior.

    Methods:
        to_messages(question, answer): Converts a question-answer pair into message format for LLM context.
        extract_records(text, entities): Performs iterative entity extraction with gleaning passes.

    The gleaning process:
    1. Performs initial entity extraction using the parent class approach
    2. For each gleaning iteration:
       - Asks the LLM to find additional entities based on previous context
       - Checks if new entities were found
       - Asks if the process should continue
       - Stops early if no new entities found or continuation not needed
    3. Combines all extracted entities from all iterations
    4. Parses and returns the final collection of entity records
    """

    def __init__(self, llm: LLMBase = None, max_glean: int = 3):
        super().__init__(llm)
       
        self._max_glean = max_glean

    def to_messages(self, question, answer) -> list[dict]:
        return [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]

    async def extract_records(
        self, text: str, entities: list[str] = None
    ) -> list[list] | None:
        # fall back to basic extraction if max_glean is 1 or less
        if self._max_glean <= 1:
            return await super().extract_records(text, entities=entities)

        if not text or text.strip() == "":
            return None
        extraction_prompt = self.get_extraction_prompt(            text, entity_types=entities
        )
        found = await self.llm.ask(
            question=extraction_prompt, key=text, category="graph-extraction"
        )
        if not found or found.answer.strip() == "":
            return None
        # the extra messages are the basic extraction plus iterations
        extra_messages = self.to_messages(extraction_prompt, found.answer)
        accumulated_entities = found.answer.strip()
        # at this point we have the same as the basic extraction
        iteration_prompt = prompts.extraction.iterate_entity_extraction()
        for glean_index in range(self._max_glean):
            glean = await self.llm.ask(
                question=iteration_prompt,
                extra_messages=extra_messages,
                key=str(glean_index),
                category="gleaning",
            )
            glean_answer = glean.answer.strip()
            log(f"Glean iteration {glean_index} answer: {glean_answer}")
            if glean_answer == "" or glean_answer.endswith("No new entities found."):
                break
            if glean_index == self._max_glean - 1:
                break
            # add the glean answer to the extra messages for the next iteration
            extra_messages += self.to_messages(iteration_prompt, glean_answer)
            # note that the split_string_by_multi_markers will take care of markers and stuff, no need to take care of the final <|COMPLETE|> and such
            accumulated_entities += "\n" + glean_answer
            # after each glean, ask if we need to continue?
            check_break = await self.llm.ask(
                question=prompts.extraction.glean_break,
                extra_messages=extra_messages,
                key=str(glean_index) + "-break",
                category="glean-break",
            )
            check_break_answer = check_break.answer.strip().lower()
            if check_break_answer.strip().strip('"').strip("'").lower() != "yes":
                break

        return answer_to_records(accumulated_entities)

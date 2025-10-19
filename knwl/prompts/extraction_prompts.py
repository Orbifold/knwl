import os.path

from knwl.prompts.prompt_constants import PromptConstants

current_dir = os.path.dirname(os.path.abspath(__file__))


class ExtractionPrompts:
    def __init__(self):
        self._fast_entity_extraction_template = None
        self._full_entity_extraction_template = None
        self._iterate_entity_template = None
        self._glean_break_template = None
        self._keywords_extraction_template = None

    def fast_graph_extraction(self, text: str, entity_types: list[str] = None) -> str:
        if self._fast_entity_extraction_template is None:
            with open(
                os.path.join(current_dir, "templates", "fast_graph_extraction.txt"),
                "r",
            ) as f:
                self._fast_entity_extraction_template = f.read()
        return self._fast_entity_extraction_template.format(
            tuple_delimiter=PromptConstants.DEFAULT_TUPLE_DELIMITER,
            record_delimiter=PromptConstants.DEFAULT_RECORD_DELIMITER,
            completion_delimiter=PromptConstants.DEFAULT_COMPLETION_DELIMITER,
            entities=", ".join(entity_types or PromptConstants.DEFAULT_ENTITY_TYPES),
            text=text,
        )

    def full_graph_extraction(self, text: str, entity_types: list[str] = None) -> str:
        if self._full_entity_extraction_template is None:
            with open(
                os.path.join(current_dir, "templates", "full_graph_extraction.txt"),
                "r",
            ) as f:
                self._full_entity_extraction_template = f.read()
        return self._full_entity_extraction_template.format(
            tuple_delimiter=PromptConstants.DEFAULT_TUPLE_DELIMITER,
            record_delimiter=PromptConstants.DEFAULT_RECORD_DELIMITER,
            completion_delimiter=PromptConstants.DEFAULT_COMPLETION_DELIMITER,
            entities=", ".join(entity_types or PromptConstants.DEFAULT_ENTITY_TYPES),
            text=text,
        )
    def fast_entity_extraction(self, text: str, entity_types: list[str] = None) -> str:
        if self._fast_entity_extraction_template is None:
            with open(
                os.path.join(current_dir, "templates", "fast_entity_extraction.txt"),
                "r",
            ) as f:
                self._fast_entity_extraction_template = f.read()
        return self._fast_entity_extraction_template.format(
            tuple_delimiter=PromptConstants.DEFAULT_TUPLE_DELIMITER,
            record_delimiter=PromptConstants.DEFAULT_RECORD_DELIMITER,
            completion_delimiter=PromptConstants.DEFAULT_COMPLETION_DELIMITER,
            entities=", ".join(entity_types or PromptConstants.DEFAULT_ENTITY_TYPES),
            text=text,
        )
    def keywords_extraction(self, text: str) -> str:
        if self._keywords_extraction_template is None:
            with open(
                os.path.join(current_dir, "templates", "keywords_extraction.txt"),
                "r",
            ) as f:
                self._keywords_extraction_template = f.read()
        return self._keywords_extraction_template.format(text=text)
    
    def iterate_entity_extraction(self) -> str:
        if self._iterate_entity_template is None:
            with open(
                os.path.join(current_dir, "templates", "iterate_entity_extraction.txt"),
                "r",
            ) as f:
                self._iterate_entity_template = f.read()
        return self._iterate_entity_template

    @property
    def glean_break(self) -> str:
        if self._glean_break_template is None:
            with open(
                os.path.join(current_dir, "templates", "glean_break.txt"), "r"
            ) as f:
                self._glean_break_template = f.read()
        return self._glean_break_template


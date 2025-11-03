import os.path

from knwl.prompts.prompt_constants import PromptConstants

current_dir = os.path.dirname(os.path.abspath(__file__))


class RagPrompts:
    def __init__(self):
        self._self_rag_prompt = None

    def self_rag(self, question: str) -> str:
        if self._self_rag_prompt is None:
            with open(os.path.join(current_dir, "templates", "self_rag.txt"), "r") as f:
                self._self_rag_prompt = f.read()
        return self._self_rag_prompt.format(
            text=question,
            record_delimiter=PromptConstants.DEFAULT_RECORD_DELIMITER,
            completion_delimiter=PromptConstants.DEFAULT_COMPLETION_DELIMITER,
        )

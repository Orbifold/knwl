import os.path

current_dir = os.path.dirname(os.path.abspath(__file__))


class SummarizationPrompts:
    def __init__(self):
        self._summarize_template = None
        self._summarize_entity_template = None

    def summarize(self, text: str) -> str:
        """
        Generate a summarization prompt by formatting text into a template.

        This method loads a summarization template from 'summarize.txt' file if not already
        cached, then formats the provided text into the template to create a prompt suitable
        for text summarization tasks.

        Args:
            text (str): The input text to be summarized. Must not be None or empty.

        Returns:
            str: A formatted prompt string ready for summarization processing.

        Raises:
            ValueError: If the input text is None or empty (whitespace only).

        Note:
            The summarization template is loaded once and cached for subsequent calls
            to improve performance.
        """
        if text is None or text.strip() == "":
            raise ValueError("Input text for summarization cannot be empty.")
        if self._summarize_template is None:
            with open(os.path.join(current_dir, "templates", "summarize.txt"), "r") as f:
                self._summarize_template = f.read()

        return self._summarize_template.format(text=text)

    def summarize_entity(self, entities: str | list[str], description: str | list[str]) -> str:
        if entities is None:
            raise ValueError("Entities for summarization cannot be empty. Use the general summarize method instead.")

        if isinstance(entities, list):
            entities = ", ".join(entities)
        if entities.strip() == "":
            raise ValueError("Entities for summarization cannot be empty. Use the general summarize method instead.")
        if description is None:
            raise ValueError("Description for entity summarization cannot be empty.")
        if isinstance(description, list):
            description = " ".join(description)
        if description.strip() == "":
            raise ValueError("Description for entity summarization cannot be empty.")
        if self._summarize_entity_template is None:
            with open(os.path.join(current_dir, "templates", "summarize_entity.txt"), "r") as f:
                self._summarize_entity_template = f.read()
        return self._summarize_entity_template.format(entities=entities, description=description)

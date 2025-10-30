from knwl import services, KnwlIngestion, KnwlInput, GraphRAG, KnwlAnswer
from knwl.models.KnwlParams import AugmentationStrategy


class Knwl:
    """
    Utility class wrapping various functionalities without having to instantiate or configure anything.
    """

    def __init__(self):

        self.grag = GraphRAG()
        self._llm = None

    @property
    def llm(self):
        """
        Get the LLM client used by Knwl.
        """
        if self._llm is None:
            self._llm = services.get_service("llm")
        return self._llm

    async def add(self, input: str | KnwlInput) -> KnwlIngestion:
        """
        Add input to be processed by Knwl.
        """
        if isinstance(input, str):
            input = KnwlInput(text=input)

        return await self.grag.ingest(input)

    async def ask(
        self, question: str, space: str = None, strategy: AugmentationStrategy = None
    ) -> KnwlAnswer:
        """
         
        
        """
        if space is None:
            space = "default"
        if strategy is None:
            return await self.simple_ask(question)

    async def simple_ask(self, question: str) -> KnwlAnswer:
        """
        Simple LLM QA without knowledge graph.
        This uses the default LLM service configured.
        """
        found = await self.llm.ask(question)
        return found or KnwlAnswer.none()

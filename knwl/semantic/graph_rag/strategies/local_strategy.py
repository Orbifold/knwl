from knwl.semantic.graph_rag.strategies.strategy_base import GragStrategyBase


class LocalGragStrategy(GragStrategyBase):
    """
        Executes a local query and returns the response.
        The local query takes the neighborhood of the hit nodes and uses the low-level keywords to find the most related text units.

        This method performs the following steps:
        1. Extracts keywords from the given query using a predefined prompt.
        2. Attempts to parse the extracted keywords from the result.
        3. If parsing fails, attempts to clean and re-parse the result.
        4. Retrieves context based on the extracted keywords and query parameters.
        5. Constructs a system prompt using the retrieved context and query parameters.
        6. Executes the query with the constructed system prompt and returns the response.

        Args:
            query (str): The query string to be processed.
            query_param (QueryParam): An object containing parameters for the query.

        Returns:
            str: The response generated from the query. If an error occurs during processing, a failure response is returned.
        """
    def __init__(self):
        super().__init__()
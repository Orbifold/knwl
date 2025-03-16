from dataclasses import dataclass
from typing import Literal


@dataclass
class QueryParam:
    mode: Literal["local", "global", "hybrid", "naive"] = "global"

    only_need_context: bool = False

    response_type: str = "Multiple Paragraphs"

    # Number of top-k items to retrieve; corresponds to entities in "local" mode and relationships in "global" mode.
    top_k: int = 60

    # Number of tokens for the original chunks.
    max_token_for_text_unit: int = 4000

    # Number of tokens for the relationship descriptions
    max_token_for_global_context: int = 4000

    # Number of tokens for the entity descriptions
    max_token_for_local_context: int = 4000

    # Whether to return the RAG context
    return_context = True

    # Whether to return the references
    return_references = True
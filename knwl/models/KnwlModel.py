from typing import Protocol, runtime_checkable


@runtime_checkable
class KnwlModel(Protocol):
    """
    Protocol defining the interface for all KNWL models.
    
    All KNWL models are immutable Pydantic models with:
    - Auto-generated `id` field from hash of key attributes
    - `model_dump(mode="json")` for serialization
    - `model_config = {"frozen": True}` for immutability
    """
    
    id: str
    
    def model_dump(self, **kwargs) -> dict:
        """Pydantic method for serialization."""
        ...
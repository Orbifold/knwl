from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class KnwlModel(Protocol):
    """
    Protocol defining the interface for all Knwl models.
    
    All Knwl models are Pydantic models with:
    - an `id` field (from hash of key attributes or assigned)
    - `model_dump(mode="json")` for serialization
    """
    
    id: Optional[str]
    
    def model_dump(self, **kwargs) -> dict:
        """Pydantic method for serialization."""
        ...
 
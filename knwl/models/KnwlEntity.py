from pydantic import BaseModel, Field, model_validator
from typing import Optional
from knwl.utils import hash_with_prefix


class KnwlEntity(BaseModel):
    """
    A Pydantic model representing an extracted knowledge entity.

    This class models entities extracted from text processing, such as named entities
    (persons, organizations, locations) or other semantic entities. Each entity is
    uniquely identified by a hash generated from its name and type.

    Attributes:
        entity (str): The extracted entity text/name.
        type (str): The classification type of the entity (e.g., 'PERSON', 'ORG', 'GPE').
        description (Optional[str]): An optional brief description providing context about the entity.
        chunk_id (Optional[str]): The identifier of the text chunk from which this entity was extracted.
        id (str): Auto-generated unique identifier created by hashing the entity name and type with 'entity|>' prefix.

    Note:
        The `id` field is automatically populated after model validation using the entity name and type.
    """

    entity: str = Field(..., description="The extracted entity")
    type: str = Field(
        ..., description="The type of the extracted entity (e.g., PERSON, ORG, GPE)"
    )
    description: Optional[str] = Field(
        "", description="A brief description of the entity"
    )
    chunk_id: Optional[str] = Field(
        None, description="The ID of the chunk from which the entity was extracted"
    )
    id: str = Field(
        default=None,
        description="The unique identifier of the node, automatically generated from the required fields.",
        init=False,
    )

    @model_validator(mode="after")
    def update_id(self):
        object.__setattr__(
            self,
            "id",
            hash_with_prefix(self.entity + " " + self.type, prefix="entity|>"),
        )

        return self

    def __repr__(self):
        return f"<KnwlEntity, entity={self.entity}, type={self.type}, id={self.id}>"

    def __str__(self):
        return self.__repr__()

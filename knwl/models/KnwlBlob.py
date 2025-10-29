from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, model_validator
from typing import Optional

from knwl.models import KnwlDocument, KnwlInput
from knwl.models.KnwlChunk import KnwlChunk
from knwl.utils import get_full_path, hash_with_prefix


class KnwlBlob(BaseModel):
    """
    A class representing a binary large object (BLOB).

    Attributes:
        data (bytes): The binary data of the BLOB.
        id (str): A unique identifier for the BLOB. Defaults to a new UUID.
        timestamp (str): The timestamp when the BLOB was created. Defaults to the current time in ISO format.
        typeName (str): The type name of the BLOB. Defaults to "KnwlBlob".
        name (str): The name of the BLOB. Defaults to an empty string.
        description (str): A description of the BLOB. Defaults to an empty string.
    """

    data: bytes = Field(..., description="The binary data of the BLOB")
    id: Optional[str] = Field(
        default=None, description="Unique identifier for the BLOB"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Creation timestamp",
    )
    metadata: dict = Field(default_factory=dict, description="BLOB metadata")
    description: str = Field(default="", description="BLOB description")
    name: str = Field(default="", description="BLOB name")
    type_name: str = Field(
        default="KnwlBlob",
        frozen=True,
        description="The type name of this class, for serialization purposes.",
    )

    @field_validator("data")
    def data_not_empty(cls, v):
        if v is None or len(v) == 0:
            raise ValueError("Data of a KnwlBlob cannot be None or empty.")
        return v

    @model_validator(mode="after")
    def set_id(self) -> "KnwlBlob":
        if self.id is None and self.data is not None and len(self.data) > 0:
            object.__setattr__(
                self, "id", self.hash_keys(self.data, self.name, self.description)
            )
        return self

    @staticmethod
    def hash_keys(data: bytes, name: str = None, description: str = None) -> str:
        return hash_with_prefix(
            data + b" " + (name or "").encode() + b" " + (description or "").encode(),
            prefix="blob|>",
        )

    async def save_to_file(self, path: str):
        """
        Save the BLOB data to a file. Note that the metadata is not saved.

        Args:
            path (str): The file path where the BLOB data should be saved.
        """
        path = get_full_path(path)

        with open(path, "wb") as f:
            f.write(self.data)
        return path

    @staticmethod
    async def from_file(
        path: str, name: str = None, description: str = None
    ) -> "KnwlBlob":
        """
        Load BLOB data from a file and create a KnwlBlob instance.

        Args:
            path (str): The file path from which to load the BLOB data.
            name (str, optional): The name of the BLOB. Defaults to None.
            description (str, optional): A description of the BLOB. Defaults to None.
        """
        path = get_full_path(path)

        with open(path, "rb") as f:
            data = f.read()
        return KnwlBlob(data=data, name=name, description=description)

    @staticmethod
    async def from_bytes(
        data: bytes, name: str = None, description: str = None
    ) -> "KnwlBlob":
        """
        Create a KnwlBlob instance from binary data.

        Args:
            data (bytes): The binary data for the BLOB.
            name (str, optional): The name of the BLOB. Defaults to None.
            description (str, optional): A description of the BLOB. Defaults to None.
        """
        return KnwlBlob(data=data, name=name, description=description)

    @staticmethod
    def from_input(input: KnwlInput):
        """
        Create a KnwlBlob instance from a KnwlInput object.

        Args:
            input (KnwlInput): The input object containing data, name, and description
                              to be used for creating the KnwlBlob instance.

        Returns:
            KnwlBlob: A new KnwlBlob instance initialized with the input's data,
                     name, and description.
        """
        return KnwlBlob(data=input.data, name=input.name, description=input.description)

    @staticmethod
    def from_document(document: KnwlDocument):
        """
        Create a KnwlBlob instance from a KnwlDocument.

        This class method converts a KnwlDocument into a KnwlBlob by encoding the document's
        content as UTF-8 bytes and transferring the name and description properties.

        Args:
            document (KnwlDocument): The source document to convert. Must have content,
                name, and description attributes.

        Returns:
            KnwlBlob: A new KnwlBlob instance with the document's content encoded as
                UTF-8 bytes, and the same name and description as the source document.
        """
        return KnwlBlob(
            id=document.id,
            data=document.content.encode("utf-8"),
            name=document.name,
            description=document.description,
        )

    @staticmethod
    def from_chunk(chunk: "KnwlChunk"):
        """
        Create a KnwlBlob instance from a KnwlChunk.

        This class method converts a KnwlChunk into a KnwlBlob by encoding the chunk's
        text as UTF-8 bytes and transferring the name and description properties.

        Args:
            chunk (KnwlChunk): The source chunk to convert. Must have text, name, and description attributes.
        Returns:
            KnwlBlob: A new KnwlBlob instance with the chunk's text encoded as
                UTF-8 bytes, and the same name and description as the source chunk.
        """
        return KnwlBlob(
            id=chunk.id,
            data=chunk.text.encode("utf-8"),
            name=chunk.name,
            description=chunk.description,
        )

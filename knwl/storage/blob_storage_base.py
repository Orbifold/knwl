from abc import ABC, abstractmethod

from knwl.models import KnwlBlob
from knwl.storage.storage_base import StorageBase


class BlobStorageBase(StorageBase, ABC):
    """
    Abstract base class for storing blobs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def upsert(self, blob: KnwlBlob) -> str | None: ...

    """Insert or update a KnwlBlob in the storage backend.

    If a blob with the same identifier already exists, update its stored contents; otherwise, create a new
    record. This is an asynchronous operation and must be awaited.

    Parameters
    ----------
    blob: KnwlBlob
        The blob to be inserted or updated. Implementations may require certain fields (for example, an
        identifier) to be present; if not provided, the backend may generate one.

    Returns
    -------
    str | None
        The identifier of the upserted blob on success, or None if the operation did not complete
        successfully (for example, if validation fails or the backend rejects the request).

    Raises
    ------
    ValueError
        If the provided blob is invalid (e.g., missing required fields).
    StorageError
        If the underlying storage backend fails (or a backend-specific exception may be raised).

    Notes
    -----
    Implementations should aim for atomic, idempotent behavior where possible and perform necessary
    validation before writing to the backend.
    """

    @abstractmethod
    async def get_by_id(self, id: str) -> KnwlBlob | None: ...
    """
    Asynchronously retrieve a KnwlBlob by its unique identifier.

    Args:
        id (str): The unique identifier of the blob to retrieve.

    Returns:
        KnwlBlob | None: The matching KnwlBlob if found, otherwise None.

    Raises:
        ValueError: If `id` is empty or otherwise invalid.
        OSError: If an I/O or storage backend error occurs while attempting to read the blob.

    Notes:
        Implementations should be non-blocking and return promptly. If the storage backend distinguishes
        between "not found" and other errors, this method should return None for "not found" and raise
        an appropriate exception for other failure modes.
    """

    @abstractmethod
    async def delete_by_id(self, id: str) -> bool: ...
    """Asynchronously delete a blob by its identifier.

    Args:
        id (str): The unique identifier of the blob to remove.

    Returns:
        bool: True if the blob was deleted successfully; False if no blob existed with the given id.

    Raises:
        TypeError: If `id` is not a string.
        RuntimeError: For storage-backend failures (implementation-specific).

    Notes:
        Implementations should make this operation idempotent: deleting a non-existent blob
        should return False rather than raising an exception.
    """

    @abstractmethod
    async def count(self) -> int: ...
    """
    Return the total number of items stored in this blob storage.

    This is an async coroutine and must be awaited. Implementations should return
    the exact count of blobs/objects managed by the backend. Note that retrieving
    the count may be expensive for some backends (e.g., requiring a full scan).

    Returns:
        int: The number of stored blobs.

    Raises:
        Exception: Implementation-specific errors (e.g., I/O or storage backend errors)
        that occur while computing the count.
    """

    @abstractmethod
    async def exists(self, id: str) -> bool: ...
    """Return whether a blob with the given identifier exists in storage.

    This coroutine checks if an object with the provided `id` is present in the
    storage backend. Implementations should perform an efficient existence check
    (e.g., metadata/head request) rather than downloading the object's contents.

    Args:
        id (str): Identifier of the blob to check. Must be a valid, non-empty
            identifier according to the storage's naming rules.

    Returns:
        bool: True if the blob exists, False if it does not.

    Raises:
        ValueError: If `id` is invalid (for example, empty or malformed).
        Exception: Implementation-specific backend errors (e.g., network or
            permission failures). Absence of a blob should not raise an exception;
            it should result in False.

    Notes:
        - This is an async method and must be awaited.
        - Implementations should be safe for concurrent use.
        - Document any normalization applied to `id` (case sensitivity, trimming, etc.).
    """

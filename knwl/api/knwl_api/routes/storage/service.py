from knwl.api.knwl_api.tasks import knwl
from knwl.logging import log
from knwl.models import KnwlDocument


async def document_count() -> int:
    """
    Get the total number of documents in the storage.

    Returns:
        int: Total document count
    """
    try:
        count = await knwl.document_count()
        log.debug(f"Document count retrieved: {count}")
        return count

    except Exception as e:
        log(e)
        raise

async def get_all_documents(amount: int = 10, include_content: bool = False) -> list[KnwlDocument]:
    """
    Retrieve a list of documents from storage.

    Args:
        amount (int): Number of documents to retrieve
        include_content (bool): Whether to include the content of the documents

    Returns:
        list: List of KnwlDocument instances
    """
    try:
        documents = await knwl.get_all_documents(amount=amount, include_content=include_content)
        log.debug(f"Retrieved {len(documents)} documents from storage.")
        return documents

    except Exception as e:
        log(e)
        raise
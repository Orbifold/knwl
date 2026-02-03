from typing import Dict

from fastapi import APIRouter, HTTPException, status
from knwl.api.knwl_api.models.CountResponse import CountResponse

from knwl.api.knwl_api.routes.storage import service
from knwl.models import KnwlDocument

router = APIRouter()


@router.get(
    "/document_count",
    response_model=CountResponse,
    summary="Get document count",
    description="Returns the total number of documents in the storage.",
    responses={
        200: {"description": "Successfully retrieved node count"},
        500: {"description": "Internal server error"},
    },
)
async def get_document_count() -> CountResponse:
    """
    Get the total number of documents in the storage.

    Returns:
        CountResponse: Object containing the document count

    Raises:
        HTTPException: 500 error if the operation fails
    """
    try:
        count = await service.document_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document count: {str(e)}",
        )


@router.get(
    "/documents",
    response_model=list[KnwlDocument],
    summary="Get documents",
    description="Returns a list of documents from the storage.",
    responses={
        200: {"description": "Successfully retrieved node count"},
        500: {"description": "Internal server error"},
    },
)
async def get_documents(amount: int = 10, include_content: bool = False) -> Dict:
    """
    Retrieve a list of documents from storage.

    Args:
        amount (int): Number of documents to retrieve

    Returns:
        Dict: Dictionary containing the list of documents

    Raises:
        HTTPException: 500 error if the operation fails
    """
    try:
        documents = await service.get_all_documents(
            amount=amount, include_content=include_content
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        )


@router.get(
    "/document/{document_id}",
    response_model=KnwlDocument,
    summary="Get document by Id",
    description="Retrieve a document by its Id from storage.",
    responses={
        200: {"description": "Successfully retrieved document"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_document_by_id(document_id: str) -> KnwlDocument:
    """
    Retrieve a document by its Id.

    Args:
        document_id (str): The Id of the document to retrieve

    Returns:
        KnwlDocument: The retrieved document

    Raises:
        HTTPException: 404 error if the document is not found
        HTTPException: 500 error if the operation fails
    """
    try:
        document = await service.get_document_by_id(document_id=document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with Id {document_id} not found",
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        )


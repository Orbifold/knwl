from fastapi import APIRouter, HTTPException, Query

from knwl.api.knwl_api.routes.collect import service
from knwl.models.KnwlDocument import KnwlDocument

router = APIRouter()


@router.get(
    "/wiki",
    summary="Fetch Wikipedia Article",
    description="Fetches and parses the specified Wikipedia article, returning it as a KnwlDocument with metadata.",
    response_model=KnwlDocument,
    response_description="The Wikipedia article content with title and metadata",
    responses={
        404: {"description": "Wikipedia article not found"},
        500: {"description": "Failed to fetch or parse the article"},
    },
)
async def get_wiki_article(
    title: str = Query(..., description="The title of the Wikipedia article to fetch", examples={"example": "Artificial_intelligence"}),
):
    try:
        return await service.get_wiki_article(title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/url",
    summary="Fetch URL Content",
    description="Fetches content from the specified URL and converts it to markdown format.",
    response_model=KnwlDocument,
    response_description="The webpage content converted to markdown with metadata",
    responses={
        400: {"description": "Invalid URL format"},
        404: {"description": "URL not reachable or page not found"},
        500: {"description": "Failed to fetch or parse the content"},
    },
)
async def get_url_content(
    url: str = Query(..., description="The URL to fetch content from", examples={"example": "https://discovery.graphsandnetworks.com"}),
):
    try:
        return await service.get_url_content(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
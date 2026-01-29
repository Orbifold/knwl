from fastapi import APIRouter, HTTPException
from fastapi import Request

from knwl.api.knwl_api.routes.collect import service
from knwl.models.KnwlDocument import KnwlDocument

router = APIRouter()


@router.get("/wiki", description="Fetches the specified Wikipedia article.", response_model=KnwlDocument)
async def get_wiki_article(title: str):
    try:
        return await service.get_wiki_article(title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/url", description="Fetches the content from the specified URL (as markdown).", response_model=KnwlDocument)
async def get_url_content(url: str):
    try:
        return await service.get_url_content(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
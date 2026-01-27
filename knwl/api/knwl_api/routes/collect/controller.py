from fastapi import APIRouter, HTTPException
from fastapi import Request

from knwl.api.knwl_api.routes.collect import service

router = APIRouter()


@router.get("/wiki", description="Fetches the specified Wikipedia article.")
async def get_article(title: str):
    try:
        return await service.get_article(title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

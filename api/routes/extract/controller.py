from fastapi import APIRouter, HTTPException

from api.models.JsonRequest import JsonRequest
from api.models.GraphRequest import GraphRequest
from knwl.logging import log

router = APIRouter()



@router.post("/json", summary="Extract graph as JSON. The set of entities is optional and can be used to guide the extraction.")
async def extract_json(request: JsonRequest):
    try:
        if not request.text or request.text == "":
            raise HTTPException(status_code=400, detail="text is required.")
        from knwl.services import services
        extractor = services.get_service("graph_extraction")
        found = await extractor.extract_json(request.text, request.entities)
        return found
    except Exception as e:
        log(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph", summary="Extract graph as graph object. The set of entities is optional and can be used to guide the extraction. The chunk_id is optional and can be used to tag the extraction with a specific chunk identifier.")
async def extract_graph(request: GraphRequest):
    try:
        if not request.text or request.text == "":
            raise HTTPException(status_code=400, detail="text is required.")
        from knwl.services import services
        extractor = services.get_service("graph_extraction")
        found = await extractor.extract_graph(request.text, request.entities, request.chunk_id)
        return found
    except Exception as e:
        log(e)
        raise HTTPException(status_code=500, detail=str(e))

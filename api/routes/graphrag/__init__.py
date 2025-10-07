

def register_graphrag_routes(app):
    from api.routes.graphrag.controller import router as graphrag_router

    app.include_router(graphrag_router, prefix=f"/graphrag", tags=["GraphRag"])

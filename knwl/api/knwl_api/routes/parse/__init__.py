

def register_parse_routes(app):
    from .controller import router as app_router

    app.include_router(app_router, prefix=f"/parse", tags=["parse"])
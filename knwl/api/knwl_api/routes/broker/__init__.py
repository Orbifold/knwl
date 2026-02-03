def register_broker_routes(app):
    from .controller import router as app_router

    app.include_router(app_router, prefix=f"/broker", tags=["broker"])
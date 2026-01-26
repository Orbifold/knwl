from .routes import register_routes


# ============================================================
# Create the FastAPI application instance.
# This is used by unit tests to instantiate the app.
# ============================================================
def create_app():
    from fastapi import FastAPI
    from starlette.responses import PlainTextResponse

    app = FastAPI(title="Knwl API")
    # app.add_middleware(BaseHTTPMiddleware, dispatch=authentication_middleware)
    register_routes(app)

    @app.get("/", response_class=PlainTextResponse)
    def index():
        return f"Knwl API"

    return app

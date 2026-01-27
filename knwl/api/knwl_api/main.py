from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from starlette.responses import JSONResponse

knwl_version = version("knwl")

from knwl.api.knwl_api.routes import register_routes
from knwl.api.knwl_api.mcp_server import mcp_app
from knwl.api.knwl_api.taskiq_broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Combined lifespan for MCP and TaskIQ"""
    # Startup: Initialize TaskIQ broker
    if not broker.is_worker_process:
        await broker.startup()

    # Use MCP's lifespan context
    async with mcp_app.lifespan(app):
        yield

    # Shutdown: Clean up TaskIQ broker
    if not broker.is_worker_process:
        await broker.shutdown()


# @formatter:off
app = FastAPI(
    title="Knwl API",
    summary="Knwl Web Services",
    version=knwl_version,
    description="This API is a wrapper around the Knwl class and can be used to interact with your knowledge graph, see <a href='http://knwl.ai' target='_blank' title='Knwl AI'>http://knwl.ai</a>.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-qa-Id",  # custom header for QA ID
        "X-service-name",  # custom header for AZ service name
        "X-from-cache",  # when using load testing
    ],
)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns a welcome message.
    """
    return JSONResponse(f"Knwl API v{knwl_version}. Swagger at /docs and ReDoc at /redoc.", status_code=200)


@app.get("/info", tags=["Info"])
async def info():
    """
    Info endpoint that returns project information.
    """
    return JSONResponse(f"Knwl API v{knwl_version}. Swagger at /docs and ReDoc at /redoc.", status_code=200)

# app.add_middleware(BaseHTTPMiddleware, dispatch=authentication_middleware)
register_routes(app)

# Mount MCP app at root - it provides /mcp route
# app.mount("/", mcp_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)

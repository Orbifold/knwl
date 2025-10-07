from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from api.routes import register_routes
from knwl import utils

app = FastAPI(
    title="Knwl API",
    summary=utils.get_project_info()["description"],
    version=utils.get_project_info()["version"],
    description="The web services are a wrapper around the Knwl library to provide easy access to its functionalities via RESTful APIs.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)
origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns a welcome message.
    """
    return JSONResponse(utils.get_project_info(), status_code=200)


@app.get("/info", tags=["Info", "Root"])
async def info():
    """
    Info endpoint that returns project information.
    """
    return JSONResponse(utils.get_project_info(), status_code=200)


register_routes(app)

if __name__ == "__main__":
    import uvicorn
    import os
    from knwl.config import get_config

    host = get_config("api", "host", default="0.0.0.0")
    port = int(str(get_config("api", "port", default="9000")))
    development = str(get_config("api", "development", default=True)).lower() == "true"

    if development:
        uvicorn.run(
            "knwl.api.main:app", host=host, port=port, reload=True, workers=1
        )  # note that FastAPI reload only works with 1 worker
    else:
        uvicorn.run(
            "knwl.api.main:app",
            host=host,
            port=port,
            reload=False,
            workers=os.cpu_count() * 2,
        )  # number of workers = 2 x number of CPU cores is the recommended setting

from fastapi import FastAPI
from .graphrag import register_graphrag_routes


def register_routes(app: "FastAPI") -> None:
    register_graphrag_routes(app)

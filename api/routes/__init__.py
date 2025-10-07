from fastapi import FastAPI
from .extract import register_graphrag_routes


def register_routes(app: "FastAPI") -> None:
    register_graphrag_routes(app)

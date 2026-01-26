from fastapi import FastAPI

from .kg import register_kg_routes


def register_routes(app: "FastAPI") -> None:
    register_kg_routes(app)

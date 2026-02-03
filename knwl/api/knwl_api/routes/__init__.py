from fastapi import FastAPI

from knwl.api.knwl_api.routes.collect import register_collect_routes
from knwl.api.knwl_api.routes.kg import register_kg_routes
from knwl.api.knwl_api.routes.storage import register_storage_routes
from knwl.api.knwl_api.routes.parse import register_parse_routes
from knwl.api.knwl_api.routes.broker import register_broker_routes

from knwl.knwl import Knwl


# one and only instance of Knwl for the API
knwl = Knwl()


def get_knwl() -> Knwl:
    """ """
    return knwl


def register_routes(app: "FastAPI") -> None:
    register_kg_routes(app)
    register_collect_routes(app)
    register_storage_routes(app)
    register_parse_routes(app)
    register_broker_routes(app)
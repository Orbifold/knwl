from importlib.metadata import version, PackageNotFoundError


def get_version():
    try:
        try:
            return version("knwl")
        except PackageNotFoundError:
            return "unknown"
    except Exception:
        return "unknown"

def get_config(*keys):
    from knwl.config import get_config as knwl_get_config
    return knwl_get_config(*keys)   
    
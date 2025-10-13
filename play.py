from knwl.di import inject_config
from knwl.config import default_config
default_config["a"] = {"b": "I'm a.b"}

@inject_config("a.b",  param_name="who")
def ask(who):
    return who

print(ask())  # Output: I'm a.b
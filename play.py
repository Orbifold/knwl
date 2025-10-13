from knwl.di import inject_config
from knwl.config import default_config
default_config["a"] = {"b": "I'm a.b"}

@inject_config("a.b",  param_name="who")
class Thing:
    def __init__(self, who=None):
        self.who = who

print(Thing().who)  # Output: I'm a.b
t = Thing(who="Swa")
assert isinstance(t, Thing)
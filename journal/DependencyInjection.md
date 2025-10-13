Dependency Injection (DI) is a design pattern that allows a class or function to receive its dependencies from an external source rather than creating them itself. This promotes loose coupling and enhances testability and maintainability of code.

## Injecting Configuration

Knwl has a default configuration allowing you to run things out of the box. For example, the default LLM is set to use Ollama with Qwen 2.5.

There are two ways to tune the configuration:

- all DI methods have an `override` parameter that allows you to pass a configuration dictionary that will override the default configuration for that specific function or class. Override here means actually 'deep merge' so you only need to specify the parts you want to change.
- you can modify the `knwl.config.default_config` dictionary directly to change the default configuration for the entire application. You can see an example of this below.

## Injecting Services

A simple example illustrate how it works and at the same time shows that the DI framework in Knwl can be used independently:

```python
from knwl.di import service

class Pizza:
    def __init__(self, *args, **kwargs):
        self._size = kwargs.get("size", "medium")
        self._price = kwargs.get("price", 10.00)
        self._name = kwargs.get("name", "pizza")

    def size(self):
        return self._size

    def price(self):
        return self._price

    def name(self):
        return self._name

sett = {
    "food": {
        "default":"pizza",
        "pizza": {
            "class": "__main__.Pizza",
            "size": "large",
            "price": 13.99,
            "name": "pizza",
        }
    }
}

@service("food", override=sett, param_name="kitchen")
def prepare(kitchen=None):
    if kitchen is None:
        raise ValueError("Kitchen service not injected")
    return f"Prepared a {kitchen.size()} {kitchen.name()} costing ${kitchen.price()}"


print(prepare()) # Output: Prepared a large pizza costing $13.99

```

A service `food` is defined in a configuration dictionary and the default food service is set to `pizza`. The `Pizza` class is a simple class with a method `price` that returns the price of the pizza.

The `prepare` function is decorated with the `@service` decorator, which injects the `kitchen` parameter with an instance of the `Pizza` class based on the configuration provided in `sett`. When `prepare()` is called, it uses the injected `kitchen` service to get the size and price of the pizza.
The configuration also defines a couple of named parameters that are passed to the `Pizza` constructor when the service is instantiated. This allows one to completely change the behavior of the `prepare` function by simply changing the configuration, without modifying the function itself.

Adding Chinese food would be as simple as:

```python

class Chinese:
    def __init__(self, *args, **kwargs):
        self._size = kwargs.get("size", "medium")
        self._price = kwargs.get("price", 7.00)
        self._name = kwargs.get("name", "chinese food")

    def size(self):
        return self._size

    def price(self):
        return self._price

    def name(self):
        return self._name
sett = {
    "food": {
        "default":"chinese",
        "pizza": {
            "class": "__main__.Pizza",
            "size": "large",
            "price": 13.99,
            "name": "pizza",
        },
        "chinese": {
            "class": "__main__.Chinese",
            "size": "small",
            "price": 8.99,
            "name": "noodles",
        },
    }
}
```

## Injecting Singleton Services

Note that DI does not force you to create instances via configuration. You can still create instances directly and pass them to functions if you prefer. DI simply provides a flexible way to manage dependencies when needed.

The above example will inject a new instance every time `prepare` is called. If you want to use a singleton instance instead, you can use the `@singleton_service` decorator:

```python
@singleton_service("food", override=sett, param_name="a")
@singleton_service("food", override=sett, param_name="b")
def prepare(a=None, b=None):
    assert a is b, "Singleton instances are not the same!"
    return a

food1 = prepare()
food2 = prepare()
assert food1 is food2, "Singleton instances are not the same!"
```

The magic happens via the DI framework `container` which keeps track of all services and their instances.

## Ad-hoc Classes and Functions

You can define ad-hoc classes, functions, or even instances directly in the configuration:

```python
from knwl.di import service, singleton_service


class Car:
    def __init__(self, make="Toyota", model="Corolla"):
        self.make = make
        self.model = model

    def __repr__(self):
        return f"Car(make={self.make}, model={self.model})"


sett = {
    "vehicle": {
        "default": "car",
        "car": {
            "class": Car,
            "make": "Honda",
            "model": "Civic"
        }
    }
}

@service("vehicle", override=sett)
def get_vehicle(vehicle=None):
    if vehicle:
        print(str(vehicle))

get_vehicle() # Output: Car(make=Honda, model=Civic)
```

With a lambda function:

```python
from knwl.di import service, singleton_service


class Car:
    def __init__(self, make="Toyota", model="Corolla"):
        self.make = make
        self.model = model

    def __repr__(self):
        return f"Car(make={self.make}, model={self.model})"


sett = {
    "vehicle": {
        "default": "car",
        "car": {
            "class": Car,
            "make": "Honda",
            "model": "Civic"
        }
    }
}

@service("vehicle", override=sett)
def get_vehicle(vehicle=None):
    if vehicle:
        print(str(vehicle))

get_vehicle() # Output: Car(make=Toyota, model=Corolla)
```

## Cascading Dependencies

Services can depend on other services. The DI framework will resolve these dependencies automatically:

```python

from knwl.di import service, singleton_service

sett = {
    "vehicle": {
        "default": "car",
        "car": {"class": "__main__.Car", "make": "Honda", "model": "Civic"},
    },
    "engine": {
        "default": "v6",
        "v6": {"class": "__main__.Engine", "horsepower": 300},
        "v4": {"class": "__main__.Engine", "horsepower": 150},
    },
}


class Engine:
    def __init__(self, horsepower=150):
        self.horsepower = horsepower

    def __repr__(self):
        return str(self.horsepower)


@service("engine", override=sett)
class Car:
    def __init__(self, engine=None):
        self._engine = engine

    def __repr__(self):
        return f"Car(engine={self._engine})"



@service("vehicle", override=sett)
def get_vehicle(vehicle=None):
    if vehicle:
        print(str(vehicle))


get_vehicle()
# Output: Car(engine=300)
```

## Inecting Configuration Values

The DI framework can inject configuration values, not just services. This is useful for injecting settings or parameters into functions or classes:

```python
from knwl.di import service, singleton_service, inject_config

sett = {
    "not_found": {
        "short": "Sorry, I can't help with that.",
        "long": "I'm sorry, but I don't have the information you're looking for.",
    }
}
@inject_config("not_found.long", override=sett, param_name="not_found")
def ask(not_found):
    return not_found

print(ask())  # Output: I'm sorry, but I don't have the information you're looking for.
```

## Default Configuration

In all the examples above, we passed an `override` parameter to the decorators to provide configuration. In a real application, you would typically load configuration from a file or environment variables and set it in the DI container at application startup:

```python
from knwl.di import inject_config
from knwl.config import default_config
default_config["a"] = {"b": "I'm a.b"}

@inject_config("a.b",  param_name="who")
def ask(who):
    return who

print(ask())  # Output: I'm a.b
```

You can also completely replace the `default_config` dictionary if needed.

## Direct Access to Services

The DI container makes use of dynamic instantiation which you can also use directly if needed:

```python
import asyncio
from knwl import services

async def main():
	s = services.get_service("llm")
	result = await s.ask("What is the Baxter equation?")
	print(result.answer)

asyncio.run(main())
```

The `get_service` looks up the `llm` service configuration and if not variation is found, the default one will be used. In this case it will use the `OllamaClient`.

A variation is simply a named configuration under the service. For example, if you had a configuration like this:

```python
sett = {
    "llm": {
        "default": "gemma",
        "gemma": {
            "class": "knwl.services.llm.ollama.OllamaClient",
            "model": "gemma3:7b"
        },
        "qwen": {
            "class": "knwl.services.llm.ollama.OllamaClient",
            "model": "Qwen2.5-7B"
        }
    }
}
```

you could use `services.get_service("llm", variation="qwen")` to get an instance of the `OllamaClient` configured to use the `Qwen2.5-7B` model instead of the default `gemma3:7b`.
This allows you to easily switch between different implementations or configurations of a service at runtime without changing the code that uses the service.

Much like the injection decorators, you can also pass an `override` parameter to `get_service` to provide ad-hoc configuration for that specific instance. You can also use `get_singleton_service` to get a singleton instance of a service. Whether you use a service via injection or directly via `get_service`, the same instance will be returned if it's a singleton service. The DI container relies on the `services` for singletons and instantiation.

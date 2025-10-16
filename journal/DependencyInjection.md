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

## Config Redirecting

Service injection happens if the parameter is not provided. If you instantiate a class in the normal Python way:

```python
engine = Engine(horsepower=110)
car = Car(engine=engine)
print(car)  # Car(engine=110)
```

the DI is still active beyond the screen but nothing will be injected since the parameter is already provided. It supplies defaults only.

There are situations where the constructor parameter is another services and you want to use a specific variation of that service. You can do this by using a special syntax in the configuration: `@/service_name/variant_name`. For example, if you have a `Car` class that depends on an `Engine` service, and you want to use a specific variant of the `Engine` service when creating a `Car`, you can do it like this:

```python
import asyncio
from knwl import  services, service


config = {
    "engine":{
        "default":"e240",
       "e240":{
            "class": "__main__.Engine",
            "horsepower": 240
       },
       "e690":{
            "class": "__main__.Engine",
            "horsepower": 690
       }
    },
    "car":{
        "default":"car1",
        "car1":{
            "class": "__main__.Car",
            "engine": "@/engine/e690"
        },
        "car2":{
            "class": "__main__.Car",
            "engine": "@/engine/e240"
        }
    }
}

class Engine:

    def __init__(self, horsepower=150):
        self.horsepower = horsepower

    def __repr__(self):
        return str(self.horsepower)


@service("engine", override=config)
class Car:
    def __init__(self, engine=None):
        self._engine = engine

    def __repr__(self):
        return f"Car(engine={self._engine})"


async def main():
   car = services.get_service("car", override=config)
   print(car)  # Car(engine=690)


asyncio.run(main())
```

The important bit to note here is that the output is `Car(engine=690)` even though the default engine is `e240`. This is because the `car1` configuration specifies that the `engine` parameter should be injected with the `e690` variant of the `Engine` service using the special syntax `@/engine/e690`. This allows you to control which variant of a dependent service is used when instantiating a service, providing fine-grained control over service dependencies via configuration.
If you leave out the `engine` parameter in the `car1` configuration, the default `e240` engine would be used instead.

Specifically in the context of Knwl, this allows you to define LLM instances for different actions: you can define a different LLM for summarization, another for question answering, and so on, all configurable via the configuration dictionary without changing the code. This is not just theoretical, a small LLM (say, 4b parameters) is convenient for summarization but you might want to use a larger model for more complex tasks like entity extraction. If you try gemma3:4b for entity extraction you will find that it times out while a larger model like Qwen2.5-7b works fine. Of course, if would be great to use one model to do everything but exxperience shows that every model has its strengths and weaknesses and using the right one for the job is often the best approach.

## Injecting Defaults with @defaults

The `@defaults` decorator provides a convenient way to inject default values from service configurations directly into class constructors or functions. This is particularly useful when you want all the parameters from a service configuration to be automatically injected without manually specifying each one. The `@defaults` decorator reads the configuration for the specified service and injects all matching parameters into the decorated function or class constructor. It replaces the standard way of assigning default values in the constructor with automatic injection from configuration.

While `@service` is great for injecting a single service instance, `@defaults` shines when you have a service configuration with multiple parameters that you want to inject as defaults. It reads the configuration for the specified service and injects all matching parameters into the decorated function or class constructor.

### Basic Usage

The following complete example illustrates how `@defaults` works:

```python
import asyncio
from knwl import defaults
from faker import Faker

config = {
    "generator": {
        "default": "small",
        "small": {"class": "__main__.Generator", "max_length": 50},
        "large": {"class": "__main__.Generator", "max_length": 200},
    },
    "llm": {
        "default": "my",
        "my": {"class": "__main__.MyLLM", "generator": "@/generator/large"},
    },
}

class Generator:
    def __init__(self, max_length=50):
        self.faker = Faker()
        self.max_length = max_length

    def generate(self, input):
        return self.faker.text(max_nb_chars=self.max_length)

@defaults("llm", override=config)
class MyLLM:
    def __init__(self, generator=None):
        if generator is None:
            raise ValueError("MyLLM: Generator instance must be provided.")
        if not isinstance(generator, Generator):
            raise TypeError("MyLLM: generator must be an instance of Generator.")
        self.generator = generator

    def ask(self, question):
        return f"Answer ({self.generator.max_length}): '{self.generator.generate(question)}'"
async def main():
    llm = MyLLM()
    print(llm.ask("What is a quandl?"))


asyncio.run(main())
```

In this example:

1. The decorator reads the default variant ("basic") from the `llm` configuration
2. It retrieves all parameters from `llm.my` (the default variant)
3. For the `generator` parameter, it sees the `@/generator/large` reference
4. It instantiates the large variant of the generator service and injects it.

By changing `{"class": "__main__.MyLLM", "generator": "@/generator/large"}` to `{"class": "__main__.MyLLM", "generator": "@/generator/small"}` in the config, the `MyLLM` instance would instead receive a small generator with `max_length=50`.

### Specifying a Variant

You can specify a particular variant instead of using the default:

```python
@defaults("llm", variant="ollama")
class CustomLLMProcessor:
    def __init__(self, model=None, temperature=None, context_window=None):
        # All parameters from llm.ollama config are injected:
        # model="qwen2.5:14b", temperature=0.1, context_window=32768
        self.model = model
        self.temperature = temperature
        self.context_window = context_window
```

### Ad-hoc Instances

Channging providers and settings is, hence, a matter of changing the configuration, not the code. It's also easy to define custom implementations and plugging them into the system via configuration.

In the example below, a `StaticGenerator` is defined that always returns the same text. This is useful for testing or specific use cases where you want predictable output. The instance is created directly in the configuration and injected as-is into the `MyLLM` class.

```python
import asyncio
from knwl import defaults
from faker import Faker


class Generator:
    def __init__(self, max_length=50):
        self.faker = Faker()
        self.max_length = max_length

    def generate(self, input):
        return self.faker.text(max_nb_chars=self.max_length)


class StaticGenerator(Generator):
    def __init__(self, text="Hello, World!"):
        self.text = text
        self.max_length = len(text)

    def generate(self, input):
        return self.text


config = {
    "generator": {
        "default": "small",
        "small": {"class": "__main__.Generator", "max_length": 50},
        "large": {"class": "__main__.Generator", "max_length": 200},
    },
    "llm": {
        "default": "my",
        "my": {
            "class": "__main__.MyLLM",
            "generator": StaticGenerator(),  # Direct instance
        },
    },
}


@defaults("llm", override=config)
class MyLLM:
    def __init__(self, generator=None):
        if generator is None:
            raise ValueError("MyLLM: Generator instance must be provided.")
        if not isinstance(generator, Generator):
            raise TypeError("MyLLM: generator must be an instance of Generator.")
        self.generator = generator

    def ask(self, question):
        return f"Answer ({self.generator.max_length}): '{self.generator.generate(question)}'"


async def main():
    llm = MyLLM()
    print(llm.ask("What is a quandl?"))


asyncio.run(main())

```

### Service Reference Resolution

The `@defaults` decorator automatically handles service redirection (strings starting with `@/`):

```python
# Config:
# "graph_extraction": {
#     "default": "basic",
#     "basic": {
#         "class": "knwl.extraction.BasicGraphExtraction",
#         "mode": "full",
#         "llm": "@/llm/ollama"  # Service reference
#     }
# }

@defaults("graph_extraction")
class BasicGraphExtraction:
    def __init__(self, llm=None, mode=None):
        # llm is instantiated from the llm/ollama service
        # mode is injected as the string value "full"
        self.llm = llm
        self.mode = mode
```

This allows you to reuse configurations across different services and ensures that the correct instances are injected based on the configuration.

### Parameter Filtering

The decorator _only_ injects parameters that exist in the function/constructor signature. Config values that don't match parameter names are silently ignored:

```python
# Config has: model, temperature, context_window, caching
@defaults("llm")
class SimpleProcessor:
    def __init__(self, model=None, temperature=None):
        # Only model and temperature are injected
        # caching and context_window are ignored (not in signature)
        self.model = model
        self.temperature = temperature
```

This ensures that you can define all sorts of things in the configuration without worrying that the constructor or function will break because of unexpected parameters.

### Overriding Defaults

You can still override the injected defaults when creating instances:

```python
@defaults("entity_extraction")
class FlexibleExtraction:
    def __init__(self, llm=None, custom_param="default"):
        self.llm = llm
        self.custom_param = custom_param

# Use injected defaults
extractor1 = FlexibleExtraction()

# Override the LLM
from knwl.services import services
custom_llm = services.get_service("llm", variant_name="ollama")
extractor2 = FlexibleExtraction(llm=custom_llm)

# Override a custom parameter
extractor3 = FlexibleExtraction(custom_param="custom_value")
```

### Combining with Other Decorators

The `@defaults` decorator can be combined with other DI decorators like `@inject_config`:

```python
@defaults("graph_extraction")
@inject_config("api.host", "api.port")
class AdvancedGraphExtraction:
    def __init__(self, llm=None, mode=None, host=None, port=None):
        # llm and mode injected from graph_extraction config
        # host and port injected from api config
        self.llm = llm
        self.mode = mode
        self.host = host
        self.port = port
```

When multiple decorators are used, they are applied in order from bottom to top (this is the Python default behavior). Each decorator adds its own injections, and explicitly provided arguments always take precedence.

### Using with Override

Like other DI decorators, `@defaults` supports runtime configuration overrides:

```python
custom_config = {
    "entity_extraction": {
        "basic": {
            "llm": "@/llm/gemma_small"  # Override to use different LLM
        }
    }
}

@defaults("entity_extraction", override=custom_config)
class TestExtraction:
    def __init__(self, llm=None):
        self.llm = llm
```

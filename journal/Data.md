# Data

The term "data" within Knwl refers either to [[Storage]] or to [[Models]]. Storage is the low-level mechanism for storing raw information, while Models are higher-level abstractions that define how data is structured and interacted with. A model in usually synonymous with 'Pydantic Model' but the storage also handles dictionaries, lists of strings and more.

## Data Types

Type variance easily turns into a complex jungle, especially if you start using generics. Knwl tries to keep things simple by adhering to a few basic principles:

- static typing is preferred, but dynamic typing is allowed where necessary 
- use `Any` sparingly, only when absolutely necessary
- prefer union types (e.g., `str | int`) over `Any` whenever possible
- no generics (however intellectually enticing they may be)

## Unique Identifiers

Many frameworks use uuid's as unique identifiers for models. Knwl takes a different approach by generating unique ids based on the hash of key attributes of the model. This ensures that two models with identical key attributes will have the same id, which is particularly useful for deduplication and consistency across different instances. If the user prefers to assign their own ids, they can do so by providing an `id` field when creating the model instance.
Drawback of this is that if you cache something based on a hashed id, but you don't like the content, you can't just change the id without changing the content. For instance, LLMs calls are cached and ift you want to ask the same question again (to the same model) you need to remove the cache entry. This rarely happens in practice, but is something to keep in mind. The hashed content is usually well defined on the basis of the attributes. For example, the cached LLM calls are hashed on the basis of the prompt, provider, model name and temperature. You can always change the hash definition if you really think a member should differentiate the hash.


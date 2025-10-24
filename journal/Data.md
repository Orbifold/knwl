# Data

The term "data" within Knwl refers either to [[Storage]] or to [[Models]]. Storage is the low-level mechanism for storing raw information, while Models are higher-level abstractions that define how data is structured and interacted with. A model in usually synonymous with 'Pydantic Model' but the storage also handles dictionaries, lists of strings and more.

## Data Types

Type variance easily turns into a complex jungle, especially if you start using generics. Knwl tries to keep things simple by adhering to a few basic principles:

- static typing is preferred, but dynamic typing is allowed where necessary 
- use `Any` sparingly, only when absolutely necessary
- prefer union types (e.g., `str | int`) over `Any` whenever possible
- no generics (however intellectually enticing they may be)

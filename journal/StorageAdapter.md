There are various types of storage necessary to make GRAG happen and in practice one often splits the data across different store:

- it's cheaper to store vectors without the actual data
- it's faster to keep certain things (e.g. metadata) in SQL and other in blob (typically binary data)
- use a product for what it's made for (using a graph database for blobs?)
- for testing purposes one often discards certain aspects to focus on a particular approach.

This means, however, that the multitude of data types and diverse storage types creates a chaos of data paths and configurations. See the [[Data]] article for a general discussion and how Knwl approaches the challenge.

The `StorageAdapter` is a gateway to CRUD things in one of the five storage types. The CRUD methods in `StorageAdapter` redirect the operation appropriately. For instance

```python
async def upsert(obj: Any, storage: StorageBase | list[StorageBase]):
...
```

upserts an arbitrary object to one or more stores. At least, it attempts to make the right choice since certain mapping are rather ambiguous:

- storing blobs in a graph database
- storing graphs as a dictionary
- storing large documents in SQL.

At the same time, it's OK to use a single store for multiple things or even everything during development or testing. The [[Configuration]] article discusses how to set up the storage adapters and the [[DependencyInjection]] explains how to wire everything together if you want to define your own storage. Everything in Knwl is defined via interface (Python ABCs) so you can easily swap out implementations. Every member in Knwl is async so you can access remote stores just as easily as local ones.

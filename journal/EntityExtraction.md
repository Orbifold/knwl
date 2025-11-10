Graph RAG consists of several techniques and entity extraction is typically done within the context of building a graph from text data. However, if you want to perform standalone entity extraction, you can use the `EntityExtractionService` directly.

```python
import asyncio
from knwl import  services, service



async def main():
    extractor = services.get_service("entity_extraction")
    text = """
   OpenAI, based in San Francisco, is a leading AI research lab. It was founded in 2015 by Elon Musk and Sam Altman. The company has developed several groundbreaking AI models, including GPT-3 and DALL-E. Microsoft has invested heavily in OpenAI, integrating its technology into products like Azure and Office 365. Other notable AI companies include Google DeepMind, known for AlphaGo, and Anthropic, which focuses on AI safety.
   """
    entities = ["ORG", "PERSON", "GPE", "PRODUCT"]
    results = await extractor.extract(text, entities)
    for record in results:
        print(record.model_dump_json(indent=2))

asyncio.run(main())
```

Google's [LangExtract](https://github.com/google/langextract) can also be used for entity extraction tasks. It doesn't extract relationships in a graph-sense however. It's a solution for feeding a knowledge graph from unstructured text but the relationships have to be created by other means.

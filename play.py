import asyncio
from knwl import  services, service
from knwl.llm.ollama import OllamaClient
from knwl.extraction.basic_entity_extraction import BasicEntityExtraction
from knwl.llm.openai import OpenAIClient

async def main():
    extractor = BasicEntityExtraction(llm=OpenAIClient())
    text = """
   OpenAI, based in San Francisco, is a leading AI research lab. It was founded in 2015 by Elon Musk and Sam Altman. The company has developed several groundbreaking AI models, including GPT-3 and DALL-E. Microsoft has invested heavily in OpenAI, integrating its technology into products like Azure and Office 365. Other notable AI companies include Google DeepMind, known for AlphaGo, and Anthropic, which focuses on AI safety.
   """
    entities = ["ORG", "PERSON", "GPE", "PRODUCT"]
    results = await extractor.extract(text, entities)
    for record in results:
        print(record.model_dump_json(indent=2))

asyncio.run(main())

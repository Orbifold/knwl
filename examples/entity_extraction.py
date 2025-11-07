# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %%
from knwl import services

extractor = services.get_service("entity_extraction")
text = """
OpenAI, based in San Francisco, is a leading AI research lab. It was founded in 2015 by Elon Musk and Sam Altman. The company has developed several groundbreaking AI models, including GPT-3 and DALL-E. Microsoft has invested heavily in OpenAI, integrating its technology into products like Azure and Office 365. Other notable AI companies include Google DeepMind, known for AlphaGo, and Anthropic, which focuses on AI safety.
"""
entities = ["PRODUCT"]
results = await extractor.extract(text, entities)
for record in results:
    print(record.model_dump_json(indent=2))

# %%
# ============================================================================================
# Extract and specify multiple entity types.
# ============================================================================================

entities = ["ORG", "PERSON", "GPE"]
results = await extractor.extract(text, entities)
for record in results:
    print(record.model_dump_json(indent=2))

# %%

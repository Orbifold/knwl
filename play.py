import asyncio
from knwl import BasicEntityExtraction, services, EntityExtractionBase


async def main():
    ext: BasicEntityExtraction = services.get_service("entity_extraction")
    result = await ext.extract_records("John Field was an Irish composer, he was born in Dublin.")
    for key in result:
        print(key)


asyncio.run(main())

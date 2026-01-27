from knwl.collect import WikipediaCollector


async def get_article(title: str):
    """Fetches the specified Wikipedia article."""
    return await WikipediaCollector.fetch_article(title)

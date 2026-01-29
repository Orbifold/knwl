from knwl.collect import WikipediaCollector
from knwl.collect.webpage import WebpageCollector


async def get_wiki_article(title: str):
    """Fetches the specified Wikipedia article."""
    return await WikipediaCollector.fetch_article(title)


async def get_url_content(url: str):
    """Fetches the content from the specified URL (as markdown)."""
    return await WebpageCollector.fetch_page(url)

import aiohttp
import markdownify
from knwl.models import KnwlDocument



class WebpageCollector:
    async def fetch_page(url: str) -> KnwlDocument:
        """
        Fetches the content of a webpage given its URL.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    html_content = markdownify.markdownify(text)
                    return KnwlDocument(
                        text=html_content,
                        name=url,
                        id=url,
                        description="Webpage content",
                        content=html_content,
                    )
        return None
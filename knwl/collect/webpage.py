from urllib.parse import urlparse, urlunparse

import aiohttp
import markdownify
from bs4 import BeautifulSoup
from knwl.models import KnwlDocument


class WebpageCollector:
    DEFAULT_HEADERS = {
        "User-Agent": "Knwl/1.8.0 (https://knwl.ai; info@orbifold.net)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitizes and normalizes a URL.
        Ensures the URL has a valid protocol (defaults to https if missing).
        """
        url = url.strip()
        if not url:
            raise ValueError("URL cannot be empty")

        parsed = urlparse(url)

        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

        if not parsed.netloc:
            raise ValueError(f"Invalid URL: missing host")

        return urlunparse(parsed)

    @staticmethod
    async def fetch_page(url: str) -> KnwlDocument:
        """
        Fetches the content of a webpage given its URL.
        """
        url = WebpageCollector.sanitize_url(url)
        async with aiohttp.ClientSession(headers=WebpageCollector.DEFAULT_HEADERS) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    html_content = markdownify.markdownify(text)
                    soup = BeautifulSoup(text, "html.parser")
                    html_title = soup.title.string if soup.title else url
                    return KnwlDocument(
                        text=html_content,
                        name=html_title,
                        id=url,
                        description="Webpage content",
                        content=html_content,
                    )
                elif response.status == 404:
                    raise ValueError(f"Webpage not found: {url}")
                elif response.status == 403:
                    raise ValueError(f"Access forbidden to webpage: {url}")
                else:
                    raise ValueError(
                        f"Failed to fetch webpage: {url} with status code {response.status}"
                    )
        return None

import os
import re

from crewai.tools import tool
from firecrawl import FirecrawlApp


@tool
def web_search_tool(query: str):
    """
    WebSearch for jobs on firecrawl.io
    :arg query: Search query
    """
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    response = app.search(
        query=query,
        limit=3,
        scrape_options={
            'formats': ['markdown']
        }
    )
    if not getattr(response, "data", None):
        return "Error using tool."

    cleaned_chunks = []

    for result in response.data:
        title = result["title"]
        url = result["url"]
        markdown = result["markdown"]
        cleaned = re.sub(r"\\+|\n+", "", markdown).strip()
        cleaned = re.sub(r"\[[^\]]+\]\([^\)]+\)|https?://[^\s]+", "", cleaned)
        cleaned_result = {
            "title": title,
            "url": url,
            "markdown": cleaned,
        }
        cleaned_chunks.append(cleaned_result)

    return cleaned_chunks

# web_search_tool("Java developers")
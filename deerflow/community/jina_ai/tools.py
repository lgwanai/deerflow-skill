import asyncio
import os

from langchain.tools import tool

from deerflow.community.jina_ai.jina_client import JinaClient
from deerflow.config import get_app_config
from deerflow.utils.readability import ReadabilityExtractor

readability_extractor = ReadabilityExtractor()


def _ensure_jina_api_key() -> None:
    config = get_app_config().get_tool_config("web_fetch")
    if config is not None and "api_key" in config.model_extra:
        os.environ["JINA_API_KEY"] = config.model_extra.get("api_key")


async def _async_web_fetch(url: str, timeout: int) -> str:
    jina_client = JinaClient()
    html_content = await jina_client.crawl(url, return_format="html", timeout=timeout)
    if isinstance(html_content, str) and html_content.startswith("Error:"):
        return html_content
    try:
        article = await asyncio.to_thread(readability_extractor.extract_article, html_content)
        return article.to_markdown()[:4096]
    except Exception:
        return "Error: 网页内容解析失败，请稍后重试"


@tool("web_fetch", parse_docstring=True)
def web_fetch_tool(url: str) -> str:
    """Fetch the contents of a web page at a given URL.
    Only fetch EXACT URLs that have been provided directly by the user or have been returned in results from the web_search and web_fetch tools.
    This tool can NOT access content that requires authentication, such as private Google Docs or pages behind login walls.
    Do NOT add www. to URLs that do NOT have them.
    URLs must include the schema: https://example.com is a valid URL while example.com is an invalid URL.

    Args:
        url: The URL to fetch the contents of.
    """
    _ensure_jina_api_key()
    timeout = 10
    config = get_app_config().get_tool_config("web_fetch")
    if config is not None and "timeout" in config.model_extra:
        timeout = config.model_extra.get("timeout")
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_async_web_fetch(url, timeout))
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, _async_web_fetch(url, timeout))
        return future.result()

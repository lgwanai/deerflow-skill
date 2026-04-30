import json
import logging

from langchain.tools import tool
from tavily import TavilyClient

from deerflow.config import get_app_config

logger = logging.getLogger(__name__)


def _get_tavily_client() -> TavilyClient:
    config = get_app_config().get_tool_config("web_search")
    api_key = None
    if config is not None and "api_key" in config.model_extra:
        api_key = config.model_extra.get("api_key")
    return TavilyClient(api_key=api_key)


@tool("web_search", parse_docstring=True)
def web_search_tool(query: str) -> str:
    """Search the web.

    Args:
        query: The query to search for.
    """
    config = get_app_config().get_tool_config("web_search")
    max_results = 5
    if config is not None and "max_results" in config.model_extra:
        max_results = config.model_extra.get("max_results")

    try:
        client = _get_tavily_client()
        res = client.search(query, max_results=max_results)
        normalized_results = [
            {
                "title": result["title"],
                "url": result["url"],
                "snippet": result["content"],
            }
            for result in res["results"]
        ]
        json_results = json.dumps(normalized_results, indent=2, ensure_ascii=False)
        return json_results
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return json.dumps({"error": "搜索服务暂时不可用，请稍后重试"}, ensure_ascii=False)


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
    try:
        client = _get_tavily_client()
        res = client.extract([url])
        if "failed_results" in res and len(res["failed_results"]) > 0:
            logger.warning("Web fetch failed for %s", url)
            return "Error: 网页获取失败，请稍后重试"
        elif "results" in res and len(res["results"]) > 0:
            result = res["results"][0]
            return f"# {result['title']}\n\n{result['raw_content'][:4096]}"
        else:
            return "Error: 未找到网页内容"
    except Exception as e:
        logger.error("Web fetch failed: %s", e)
        return "Error: 网页获取失败，请稍后重试"

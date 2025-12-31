"""
Web Tools for GLM Agent
========================

Implements web access: WebFetch and WebSearch.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def execute_web_fetch(args: dict[str, Any]) -> dict:
    """
    Fetch content from a URL.
    
    Args:
        args: {"url": str}
    
    Returns:
        {"content": str, "url": str} or {"error": str}
    """
    try:
        url = args.get("url")
        if not url:
            return {"error": "Missing required parameter: url"}
        
        # Check if httpx is available
        try:
            import httpx
        except ImportError:
            return {
                "error": "httpx not installed. Install with: pip install httpx",
                "url": url
            }
        
        # Fetch URL
        logger.info(f"Fetching URL: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content = response.text
            logger.info(f"Fetched {len(content)} bytes from {url}")
            
            return {
                "content": content,
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", "")
            }
        
    except Exception as e:
        logger.error(f"WebFetch failed: {e}")
        return {"error": str(e), "url": args.get("url")}


async def execute_web_search(args: dict[str, Any]) -> dict:
    """
    Perform a web search.
    
    Note: GLM 4.7 has built-in web search capability via tools API.
    This is a fallback implementation using DuckDuckGo.
    
    Args:
        args: {"query": str, "max_results": int (optional, default 5)}
    
    Returns:
        {"results": list[dict], "query": str} or {"error": str}
    """
    try:
        query = args.get("query")
        max_results = args.get("max_results", 5)
        
        if not query:
            return {"error": "Missing required parameter: query"}
        
        # Check if duckduckgo_search is available
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {
                "error": (
                    "duckduckgo_search not installed. "
                    "Install with: pip install duckduckgo-search\n"
                    "Or use GLM's built-in web_search tool instead."
                ),
                "query": query,
                "note": "GLM 4.7 has native web_search - prefer using that via tools API"
            }
        
        logger.info(f"Searching: {query}")
        
        # Perform search
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
        
        logger.info(f"Found {len(results)} results for: {query}")
        
        return {
            "results": results,
            "query": query,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"WebSearch failed: {e}")
        return {"error": str(e), "query": args.get("query")}

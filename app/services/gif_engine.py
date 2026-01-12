"""
GIF Engine
Combines AI query generation with Giphy search to find relevant GIFs for news articles
"""
from typing import List, Dict, Any
from app.services.giphy_service import search_gifs
from app.services.gif_ai_service import generate_gif_queries


async def get_gifs_for_news(title: str, summary: str = "", limit: int = 12) -> List[Dict[str, str]]:
    """
    Get relevant GIFs for a news article using AI-generated search queries
    
    Args:
        title: Article title
        summary: Article summary/content
        limit: Maximum number of GIFs to return
    
    Returns:
        List of GIF objects with id, url, and preview
    """
    # Generate AI-powered search queries
    queries = await generate_gif_queries(title, summary)
    print(f"[GIF Engine] Generated queries: {queries}")
    
    all_gifs = []
    seen_ids = set()
    
    # Search for each query
    for query in queries:
        try:
            gifs = await search_gifs(query, limit=6)
            for gif in gifs:
                if gif["id"] not in seen_ids:
                    seen_ids.add(gif["id"])
                    all_gifs.append(gif)
        except Exception as e:
            print(f"[GIF Engine] Error searching for '{query}': {e}")
            continue
    
    # Format and return the best GIFs
    formatted_gifs = []
    for gif in all_gifs[:limit]:
        try:
            formatted_gifs.append({
                "id": gif["id"],
                "url": gif["images"]["downsized"]["url"],
                "preview": gif["images"]["fixed_width_small"]["url"],
                "title": gif.get("title", ""),
                "width": gif["images"]["downsized"].get("width", ""),
                "height": gif["images"]["downsized"].get("height", "")
            })
        except KeyError:
            continue
    
    return formatted_gifs


async def search_gifs_direct(query: str, limit: int = 12) -> List[Dict[str, str]]:
    """
    Direct GIF search without AI query generation
    
    Args:
        query: Search term
        limit: Maximum number of GIFs to return
    
    Returns:
        List of GIF objects
    """
    try:
        gifs = await search_gifs(query, limit=limit)
        
        formatted_gifs = []
        for gif in gifs:
            try:
                formatted_gifs.append({
                    "id": gif["id"],
                    "url": gif["images"]["downsized"]["url"],
                    "preview": gif["images"]["fixed_width_small"]["url"],
                    "title": gif.get("title", ""),
                    "width": gif["images"]["downsized"].get("width", ""),
                    "height": gif["images"]["downsized"].get("height", "")
                })
            except KeyError:
                continue
        
        return formatted_gifs
    except Exception as e:
        print(f"[GIF Engine] Direct search error: {e}")
        return []

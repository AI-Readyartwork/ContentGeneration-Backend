"""
Giphy API Service
Searches for GIFs using the Giphy API
"""
import os
import httpx
from typing import List, Dict, Any

GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")


async def search_gifs(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    """
    Search for GIFs on Giphy
    
    Args:
        query: Search term
        limit: Maximum number of results (default 12)
    
    Returns:
        List of GIF data from Giphy API
    """
    if not GIPHY_API_KEY:
        raise ValueError("GIPHY_API_KEY not configured")
    
    url = "https://api.giphy.com/v1/gifs/search"
    params = {
        "api_key": GIPHY_API_KEY,
        "q": query,
        "limit": limit,
        "rating": "pg",
        "lang": "en"
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()["data"]


async def get_trending_gifs(limit: int = 12) -> List[Dict[str, Any]]:
    """
    Get trending GIFs from Giphy
    
    Args:
        limit: Maximum number of results
    
    Returns:
        List of trending GIF data
    """
    if not GIPHY_API_KEY:
        raise ValueError("GIPHY_API_KEY not configured")
    
    url = "https://api.giphy.com/v1/gifs/trending"
    params = {
        "api_key": GIPHY_API_KEY,
        "limit": limit,
        "rating": "pg"
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()["data"]

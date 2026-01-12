"""
GIF API Routes
Endpoints for searching and getting AI-recommended GIFs
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.services.gif_engine import get_gifs_for_news, search_gifs_direct

router = APIRouter(prefix="/gifs", tags=["gifs"])


class GifSearchRequest(BaseModel):
    title: str
    summary: Optional[str] = ""


@router.post("/smart-search")
async def smart_gif_search(request: GifSearchRequest):
    """
    AI-powered GIF search based on article title and summary.
    Returns GIFs that are contextually relevant to the content.
    """
    try:
        gifs = await get_gifs_for_news(
            title=request.title,
            summary=request.summary or "",
            limit=12
        )
        return {"gifs": gifs, "count": len(gifs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_gifs_endpoint(
    q: str = Query(..., description="Search query"),
    limit: int = Query(12, ge=1, le=50, description="Number of results")
):
    """
    Direct GIF search by query string.
    Use this for manual searches in the GIF picker.
    """
    try:
        gifs = await search_gifs_direct(query=q, limit=limit)
        return {"gifs": gifs, "count": len(gifs), "query": q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

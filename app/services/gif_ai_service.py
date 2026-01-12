"""
GIF AI Service
Uses AI to generate relevant GIF search queries based on news content
"""
import os
import json
import httpx
from typing import List
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_current_date_context() -> str:
    """Get current date context for AI prompts"""
    now = datetime.now()
    return f"Today is {now.strftime('%B %d, %Y')} ({now.strftime('%A')}). The current year is {now.year}."


async def generate_gif_queries(title: str, summary: str) -> List[str]:
    """
    Use AI to generate relevant GIF search queries based on article content
    
    Args:
        title: Article title
        summary: Article summary/content
    
    Returns:
        List of 3 search queries for Giphy
    """
    if not OPENAI_API_KEY:
        # Fallback to simple keyword extraction
        words = title.split()[:3]
        return [" ".join(words), "marketing", "business"]
    
    prompt = f"""You are choosing a GIF for a professional digital marketing newsletter.

{get_current_date_context()}

Article title: {title}
Summary: {summary[:500] if summary else 'No summary available'}

Generate 3 short Giphy search queries (2-4 words each).
They should be:
- professional and business-appropriate
- slightly fun but not childish
- relevant to the topic
- not meme-like or unprofessional

Return ONLY a JSON array of 3 strings, nothing else.
Example: ["marketing success", "digital growth", "business celebration"]"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4.1-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that generates GIF search queries. Always respond with only a JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            queries = json.loads(content)
            if isinstance(queries, list) and len(queries) >= 1:
                return queries[:3]
            
    except Exception as e:
        print(f"[GIF AI] Error generating queries: {e}")
    
    # Fallback queries based on title
    fallback = title.split()[:2] if title else ["marketing"]
    return [" ".join(fallback), "business success", "digital marketing"]

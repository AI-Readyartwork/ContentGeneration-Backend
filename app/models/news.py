"""
Pydantic models for news and newsletter data structures
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import uuid4
from enum import Enum
from datetime import datetime


class NewsCategory(str, Enum):
    """Digital marketing news categories"""
    SEO = "seo"
    PPC = "ppc"
    SOCIAL_MEDIA = "social_media"
    WEBSITE = "website"
    GENERAL = "general"


class NewsItem(BaseModel):
    """Individual news item with all metadata"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: str = "general"
    title: str
    publisher: str = "Unknown"
    published_date: Optional[str] = None
    url: str = ""
    summary: str = ""
    why_it_matters: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "ignore"


class PillarRun(BaseModel):
    """A pillar generation run with items by category"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    items_by_category: Dict[str, List[NewsItem]] = Field(default_factory=dict)
    selected_ids: List[str] = Field(default_factory=list)


class NewsletterSection(BaseModel):
    """A section in the newsletter draft"""
    key: str
    title: str
    item_ids: List[str] = Field(default_factory=list)
    generated_copy: Optional[str] = None
    order: int = 0


class AIRecommendation(BaseModel):
    """AI recommendation for a newsletter section"""
    section_key: str
    section_title: str
    recommended_item_ids: List[str] = Field(default_factory=list)
    reasoning: str = ""
    suggested_copy: Optional[str] = None


class NewsletterDraft(BaseModel):
    """Complete newsletter draft"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    pillar_run_id: Optional[str] = None
    sections: List[NewsletterSection] = Field(default_factory=list)
    ai_recommendations: List[AIRecommendation] = Field(default_factory=list)


# Request/Response models for API
class FetchNewsRequest(BaseModel):
    """Request to fetch news for categories"""
    categories: List[str] = Field(default_factory=lambda: ["seo", "ppc", "social_media", "website"])
    num_items_per_category: int = 4


class FetchNewsResponse(BaseModel):
    """Response with fetched news items"""
    items_by_category: Dict[str, List[NewsItem]]
    total_items: int


class GenerateRecommendationsRequest(BaseModel):
    """Request to generate newsletter recommendations"""
    news_items: List[NewsItem] = Field(default_factory=list)
    selected_ids: List[str] = Field(default_factory=list)


class GenerateRecommendationsResponse(BaseModel):
    """Response with AI recommendations"""
    recommendations: List[AIRecommendation]


class GenerateArticleRequest(BaseModel):
    """Request to generate AI article"""
    main_story: NewsItem
    supporting_items: List[NewsItem] = Field(default_factory=list)
    style: str = "professional"


class GenerateArticleResponse(BaseModel):
    """Response with generated article"""
    article: str

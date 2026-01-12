"""
API routes for news fetching and newsletter generation
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.services.news_service import NewsService
from app.services.newsletter_service import NewsletterService
from app.models.news import NewsItem
from pydantic import BaseModel, Field

router = APIRouter()
news_service = NewsService()
newsletter_service = NewsletterService()


# Flexible NewsItem for requests
class NewsItemInput(BaseModel):
    id: str
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


def to_news_item(input_item: NewsItemInput) -> NewsItem:
    """Convert NewsItemInput to NewsItem"""
    return NewsItem(
        id=input_item.id,
        category=input_item.category,
        title=input_item.title,
        publisher=input_item.publisher,
        published_date=input_item.published_date,
        url=input_item.url,
        summary=input_item.summary,
        why_it_matters=input_item.why_it_matters,
        action_items=input_item.action_items,
        tags=input_item.tags,
    )


# Request/Response models
class GenerateArticleRequest(BaseModel):
    main_story: NewsItemInput
    supporting_items: List[NewsItemInput] = Field(default_factory=list)
    style: str = "professional"


class GenerateArticleResponse(BaseModel):
    article: str


class GenerateStoryRequest(BaseModel):
    title: str
    summary: str = ""
    word_count: int = 450


class GenerateStoryResponse(BaseModel):
    story: str


class GenerateOneLinerRequest(BaseModel):
    title: str


class GenerateOneLinerResponse(BaseModel):
    one_liner: str


class GenerateCatchySummaryRequest(BaseModel):
    item: NewsItemInput


class GetSectionsResponse(BaseModel):
    sections: List[dict]


class SearchForSectionRequest(BaseModel):
    section_key: str
    section_title: str
    section_description: str
    num_items: int = 3


class SearchForSectionResponse(BaseModel):
    section_key: str
    items: List[NewsItem]


class SearchAllSectionsRequest(BaseModel):
    sections: List[SearchForSectionRequest]


class SectionWithNews(BaseModel):
    section_key: str
    section_title: str
    items: List[NewsItem]


class SearchAllSectionsResponse(BaseModel):
    sections: List[SectionWithNews]
    total_items: int


class GenerateRecommendationsResponse(BaseModel):
    sections: List[SectionWithNews]
    total_items: int


# Routes
@router.get("/sections", response_model=GetSectionsResponse)
async def get_newsletter_sections():
    """Get available newsletter sections (without tomorrow-top)"""
    return GetSectionsResponse(sections=newsletter_service.get_sections())


@router.post("/search-for-section", response_model=SearchForSectionResponse)
async def search_news_for_section(request: SearchForSectionRequest):
    """Search for news specifically suited for a newsletter section"""
    try:
        items = await news_service.search_news_for_section(
            section_title=request.section_title,
            section_description=request.section_description,
            num_items=request.num_items
        )
        return SearchForSectionResponse(
            section_key=request.section_key,
            items=items
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-all-sections", response_model=SearchAllSectionsResponse)
async def search_news_for_all_sections(request: SearchAllSectionsRequest):
    """Search for news for all newsletter sections at once"""
    try:
        results = []
        total = 0
        
        for section in request.sections:
            # Skip removed sections
            if section.section_key == "tomorrow-top":
                continue
                
            items = await news_service.search_news_for_section(
                section_title=section.section_title,
                section_description=section.section_description,
                num_items=section.num_items
            )
            
            results.append(SectionWithNews(
                section_key=section.section_key,
                section_title=section.section_title,
                items=items
            ))
            total += len(items)
        
        return SearchAllSectionsResponse(
            sections=results,
            total_items=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-article", response_model=GenerateArticleResponse)
async def generate_ai_article(request: GenerateArticleRequest):
    """Generate a long-form AI article (main article section)"""
    try:
        main_story = to_news_item(request.main_story)
        supporting = [to_news_item(item) for item in request.supporting_items]
        article = await newsletter_service.generate_ai_article(
            main_story=main_story,
            supporting_items=supporting,
            style=request.style
        )
        return GenerateArticleResponse(article=article)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-story", response_model=GenerateStoryResponse)
async def generate_story_content(request: GenerateStoryRequest):
    """Generate 400-500 word story for second/third story sections"""
    try:
        story = await newsletter_service.generate_story_content(
            title=request.title,
            summary=request.summary,
            word_count=request.word_count
        )
        return GenerateStoryResponse(story=story)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-one-liner", response_model=GenerateOneLinerResponse)
async def generate_one_liner(request: GenerateOneLinerRequest):
    """Generate a one-liner for Trendsetter/Top News sections"""
    try:
        one_liner = await newsletter_service.generate_one_liner(request.title)
        return GenerateOneLinerResponse(one_liner=one_liner)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-catchy-summary")
async def generate_catchy_summary(request: GenerateCatchySummaryRequest):
    """Generate a catchy summary for main story"""
    try:
        news_item = to_news_item(request.item)
        summary = await newsletter_service.generate_catchy_summary(news_item)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-recommendations", response_model=GenerateRecommendationsResponse)
async def generate_newsletter_recommendations():
    """Generate complete newsletter recommendations with catchy titles"""
    try:
        section_assignments = await news_service.generate_newsletter_recommendations()
        
        results = []
        total = 0
        
        # Updated section titles - removed tomorrow-top and main-article
        section_titles = {
            "main-story": "Main Story",
            "main-story-summary": "Main Story Summary",
            "second-story": "Second Story",
            "third-story": "Third Story",
            "trendsetter": "Trendsetter",
            "top-news": "Top Digital Marketing News",
            "links": "Links that Don't Suck",
        }
        
        for section_key, items in section_assignments.items():
            if section_key in section_titles:
                results.append(SectionWithNews(
                    section_key=section_key,
                    section_title=section_titles.get(section_key, section_key),
                    items=items
                ))
                total += len(items)
        
        return GenerateRecommendationsResponse(
            sections=results,
            total_items=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

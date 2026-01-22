"""
AI routes using LangChain for content generation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()


class NewsImpactRequest(BaseModel):
    title: str
    description: str
    source: str
    category: str


class NewsImpactResponse(BaseModel):
    whyItMatters: str
    actionItems: List[str]
    tokens_used: int


class RewriteTitleRequest(BaseModel):
    title: str


class RewriteTitleResponse(BaseModel):
    title: str


class GenerateSummaryRequest(BaseModel):
    title: str
    existing_summary: Optional[str] = None


class GenerateSummaryResponse(BaseModel):
    summary: str


class GenerateDescriptionRequest(BaseModel):
    title: str


class GenerateDescriptionResponse(BaseModel):
    description: str


class GenerateHookTitleRequest(BaseModel):
    title: str


class GenerateHookTitleResponse(BaseModel):
    hook_title: str


class GenerateMainArticleRequest(BaseModel):
    title: str
    summary: str = ""


class GenerateMainArticleResponse(BaseModel):
    article: str


class GenerateOneLinerRequest(BaseModel):
    title: str


class GenerateOneLinerResponse(BaseModel):
    one_liner: str


class GenerateEditorNoteRequest(BaseModel):
    content: str
    max_words: int = 300
    paragraphs: int = 3


class GenerateEditorNoteResponse(BaseModel):
    note: str


@router.post("/news-impact", response_model=NewsImpactResponse)
async def generate_news_impact(request: NewsImpactRequest):
    """Generate business impact analysis for a news article"""
    try:
        result = await ai_service.generate_news_impact(
            title=request.title,
            description=request.description,
            source=request.source,
            category=request.category
        )
        return NewsImpactResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite-title", response_model=RewriteTitleResponse)
async def rewrite_title(request: RewriteTitleRequest):
    """Rewrite a title to be more catchy (hook style)"""
    try:
        result = await ai_service.rewrite_title(request.title)
        return RewriteTitleResponse(title=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-hook-title", response_model=GenerateHookTitleResponse)
async def generate_hook_title(request: GenerateHookTitleRequest):
    """Generate a catchy hook-style title"""
    try:
        result = await ai_service.generate_hook_title(request.title)
        return GenerateHookTitleResponse(hook_title=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(request: GenerateSummaryRequest):
    """Generate or improve a summary for a news item"""
    try:
        result = await ai_service.generate_summary(
            title=request.title,
            existing_summary=request.existing_summary
        )
        return GenerateSummaryResponse(summary=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-description", response_model=GenerateDescriptionResponse)
async def generate_description(request: GenerateDescriptionRequest):
    """Generate a compelling description for the newsletter"""
    try:
        result = await ai_service.generate_description(request.title)
        return GenerateDescriptionResponse(description=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-main-article", response_model=GenerateMainArticleResponse)
async def generate_main_article(request: GenerateMainArticleRequest):
    """Generate the main article (600-800 words) for after Trendsetter section"""
    try:
        result = await ai_service.generate_main_article(
            title=request.title,
            summary=request.summary
        )
        return GenerateMainArticleResponse(article=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-one-liner", response_model=GenerateOneLinerResponse)
async def generate_one_liner(request: GenerateOneLinerRequest):
    """Generate a one-liner for Trendsetter/Top News sections"""
    try:
        result = await ai_service.generate_one_liner(request.title)
        return GenerateOneLinerResponse(one_liner=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-editor-note", response_model=GenerateEditorNoteResponse)
async def generate_editor_note(request: GenerateEditorNoteRequest):
    """Generate a 'Notes from the Editor' section (max 300 words, 3 paragraphs)"""
    try:
        result = await ai_service.generate_editor_note(
            content=request.content,
            max_words=request.max_words,
            paragraphs=request.paragraphs
        )
        return GenerateEditorNoteResponse(note=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

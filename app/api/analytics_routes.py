"""
ActiveCampaign Analytics API Routes

Endpoints for campaign performance analytics and reporting.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.analytics_service import get_analytics_service

router = APIRouter()


# Response Models
class CampaignSummary(BaseModel):
    """Campaign summary with key metrics"""
    id: str
    name: str
    type: str
    status: str
    sendDate: str
    createdDate: str
    totalSends: int
    totalRecipients: int
    opens: int
    uniqueOpens: int
    clicks: int
    uniqueClicks: int
    subscriberClicks: int
    hardBounces: int
    softBounces: int
    forwards: int
    uniqueForwards: int
    unsubscribes: int
    unsubReasons: int
    replies: int
    uniqueReplies: int
    socialShares: int
    openRate: float
    clickRate: float
    clickToOpenRate: float
    bounceRate: float
    unsubscribeRate: float
    forwardRate: float


class CampaignReport(CampaignSummary):
    """Detailed campaign report with subject"""
    subject: str


class LinkData(BaseModel):
    """Link click tracking data"""
    id: str
    url: str
    name: str
    clicks: int
    uniqueClicks: int


class ListSummary(BaseModel):
    """Subscriber list with count"""
    id: str
    name: str
    subscriberCount: int


class CampaignsResponse(BaseModel):
    """Response for campaigns list"""
    campaigns: List[CampaignSummary]
    total: int


class CampaignReportResponse(BaseModel):
    """Response for single campaign report"""
    campaign: CampaignReport


class LinksResponse(BaseModel):
    """Response for campaign links"""
    links: List[LinkData]


class ListsResponse(BaseModel):
    """Response for subscriber lists"""
    lists: List[ListSummary]


@router.get("/campaigns", response_model=CampaignsResponse)
async def get_campaigns(limit: int = 100, offset: int = 0):
    """
    Fetch all campaigns with performance metrics.
    
    Query params:
        limit: Number of campaigns to return (default 100)
        offset: Pagination offset (default 0)
    
    Returns:
        List of campaigns with stats
    """
    try:
        service = get_analytics_service()
        campaigns = await service.get_campaigns(limit=limit, offset=offset)
        
        return CampaignsResponse(
            campaigns=[CampaignSummary(**c) for c in campaigns],
            total=len(campaigns)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}", response_model=CampaignReportResponse)
async def get_campaign_report(campaign_id: str):
    """
    Get detailed report for a specific campaign.
    
    Path params:
        campaign_id: Campaign ID
    
    Returns:
        Detailed campaign report with all metrics
    """
    try:
        service = get_analytics_service()
        campaign = await service.get_campaign_by_id(campaign_id)
        
        return CampaignReportResponse(
            campaign=CampaignReport(**campaign)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign report: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/links", response_model=LinksResponse)
async def get_campaign_links(campaign_id: str):
    """
    Get click tracking data for campaign links.
    
    Path params:
        campaign_id: Campaign ID
    
    Returns:
        List of links with click counts (sorted by clicks desc)
    """
    try:
        service = get_analytics_service()
        links = await service.get_campaign_links(campaign_id)
        
        return LinksResponse(
            links=[LinkData(**l) for l in links]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign links: {str(e)}"
        )


@router.get("/lists", response_model=ListsResponse)
async def get_lists_with_counts():
    """
    Get all subscriber lists with contact counts.
    
    Returns:
        List of lists with subscriber counts
    """
    try:
        service = get_analytics_service()
        lists = await service.get_lists_with_counts()
        
        return ListsResponse(
            lists=[ListSummary(**l) for l in lists]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch lists: {str(e)}"
        )

"""
ActiveCampaign Analytics API Routes

Endpoints for campaign performance analytics and reporting.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.analytics_service import get_analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.get("/campaigns-list-all")
async def list_all_campaigns(
    limit: int = 500, 
    offset: int = 0,
    search: Optional[str] = None, 
    check_ids: Optional[str] = None,
    fetch_all_pages: bool = False
):
    """
    List ALL campaigns from ActiveCampaign (for debugging/identification).
    This endpoint shows all campaigns regardless of Editorial Digest filter.
    Use this to find the correct campaign IDs by name.
    
    Query params:
        limit: Number of campaigns per page (default 500, max recommended 500)
        offset: Pagination offset (default 0)
        search: Optional search term to filter by campaign name
        check_ids: Comma-separated campaign IDs to check if they exist (e.g., "330,329")
        fetch_all_pages: If true, fetches all campaigns across multiple pages (may be slow)
    """
    try:
        service = get_analytics_service()
        
        # If specific IDs requested, try to fetch them directly first (bypasses pagination)
        checked_campaigns = []
        check_errors = []
        if check_ids:
            ids_to_check = [id.strip() for id in check_ids.split(",")]
            logger.info(f"Checking specific campaign IDs: {ids_to_check}")
            for campaign_id in ids_to_check:
                try:
                    campaign = await service.get_campaign_by_id(campaign_id)
                    checked_campaigns.append(campaign)
                    logger.info(f"Successfully found campaign {campaign_id}: {campaign.get('name', 'Unknown')}")
                except Exception as e:
                    error_detail = str(e)
                    logger.error(f"Campaign {campaign_id} not found: {error_detail}")
                    check_errors.append({
                        "id": campaign_id,
                        "error": error_detail,
                        "http_status": error_detail.split("HTTP ")[-1].split()[0] if "HTTP" in error_detail else "Unknown"
                    })
                    checked_campaigns.append({
                        "id": campaign_id,
                        "name": f"[NOT FOUND: {error_detail}]",
                        "sendDate": "",
                        "status": "NOT_FOUND",
                        "totalSends": 0,
                        "uniqueOpens": 0,
                        "uniqueClicks": 0,
                    })
        
        # Fetch campaigns from API with pagination
        all_campaigns_raw = []
        if fetch_all_pages:
            # Fetch all pages
            current_offset = 0
            page_size = min(limit, 500)  # ActiveCampaign max is typically 500
            logger.info(f"Fetching all campaigns (fetch_all_pages=True), starting with offset {current_offset}")
            
            while True:
                page_campaigns = await service.get_campaigns(limit=page_size, offset=current_offset)
                if not page_campaigns:
                    break
                all_campaigns_raw.extend(page_campaigns)
                logger.info(f"Fetched {len(page_campaigns)} campaigns (total so far: {len(all_campaigns_raw)})")
                if len(page_campaigns) < page_size:
                    break  # Last page
                current_offset += page_size
        else:
            # Fetch single page
            logger.info(f"Fetching campaigns: limit={limit}, offset={offset}")
            all_campaigns_raw = await service.get_campaigns(limit=limit, offset=offset)
        
        # Return simplified list with ID, name, and date for easy identification
        campaigns_list = []
        for c in all_campaigns_raw:
            campaign_name = c.get("name", "")
            # Apply search filter if provided
            if search and search.lower() not in campaign_name.lower():
                continue
                
            campaigns_list.append({
                "id": str(c.get("id", "")),
                "name": campaign_name,
                "sendDate": c.get("sendDate", ""),
                "status": c.get("status", ""),
                "totalSends": c.get("totalSends", 0),
                "uniqueOpens": c.get("uniqueOpens", 0),
                "uniqueClicks": c.get("uniqueClicks", 0),
            })
        
        # Add checked campaigns if any
        if checked_campaigns:
            for c in checked_campaigns:
                campaigns_list.append({
                    "id": str(c.get("id", "")),
                    "name": c.get("name", ""),
                    "sendDate": c.get("sendDate", ""),
                    "status": c.get("status", ""),
                    "totalSends": c.get("totalSends", 0),
                    "uniqueOpens": c.get("uniqueOpens", 0),
                    "uniqueClicks": c.get("uniqueClicks", 0),
                })
        
        # Sort by sendDate descending (newest first)
        campaigns_list.sort(key=lambda x: x.get("sendDate", ""), reverse=True)
        
        # Remove duplicates (in case checked IDs were already in the list)
        seen_ids = set()
        unique_campaigns = []
        for c in campaigns_list:
            cid = c.get("id", "")
            if cid not in seen_ids:
                seen_ids.add(cid)
                unique_campaigns.append(c)
        
        response_data = {
            "total": len(unique_campaigns),
            "campaigns": unique_campaigns,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(all_campaigns_raw) >= limit if not fetch_all_pages else False
            },
            "note": "Use this to find campaign IDs. Look for 'Weekly Newsletter 28 January 2026' campaigns.",
            "search_applied": search if search else None,
            "ids_checked": check_ids if check_ids else None,
        }
        
        if check_errors:
            response_data["check_errors"] = check_errors
            response_data["hint"] = f"Some checked IDs failed. Errors: {[e['error'] for e in check_errors]}"
        else:
            response_data["hint"] = "Visit /api/analytics/campaigns-list-all?check_ids=330,329 to verify specific campaign IDs exist"
        
        if not fetch_all_pages and len(all_campaigns_raw) >= limit:
            response_data["pagination_hint"] = f"More campaigns available. Use ?offset={offset + limit} to get next page, or ?fetch_all_pages=true to get all campaigns"
        
        return response_data
    except ValueError as e:
        logger.error(f"Analytics service configuration error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to fetch campaigns: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )


@router.get("/config-check")
async def check_config():
    """Check if ActiveCampaign is configured (for debugging)"""
    from app.config import settings
    from app.services.analytics_service import get_analytics_service
    
    config_status = {
        "has_url": bool(settings.ACTIVECAMPAIGN_URL and settings.ACTIVECAMPAIGN_URL.strip()),
        "has_key": bool(settings.ACTIVECAMPAIGN_API_KEY and settings.ACTIVECAMPAIGN_API_KEY.strip()),
        "url_length": len(settings.ACTIVECAMPAIGN_URL) if settings.ACTIVECAMPAIGN_URL else 0,
        "key_length": len(settings.ACTIVECAMPAIGN_API_KEY) if settings.ACTIVECAMPAIGN_API_KEY else 0,
        "editorial_digest_campaign_ids": settings.editorial_digest_campaign_ids,
        "editorial_digest_campaign_name_pattern": settings.EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN,
    }
    
    try:
        service = get_analytics_service()
        config_status["service_created"] = True
        
        # Try to fetch campaigns to see what IDs we get
        try:
            all_campaigns = await service.get_campaigns(limit=10, offset=0)
            config_status["sample_campaign_ids"] = [
                {
                    "id": str(c.get("id", "")),
                    "id_type": type(c.get("id")).__name__,
                    "name": c.get("name", "")[:50],
                }
                for c in all_campaigns[:5]
            ]
            from app.api.campaign_filter import filter_campaigns
            filtered = filter_campaigns(all_campaigns)
            config_status["filtered_count"] = len(filtered)
            config_status["total_count"] = len(all_campaigns)
        except Exception as e:
            config_status["campaign_fetch_error"] = str(e)
    except ValueError as e:
        config_status["service_created"] = False
        config_status["error"] = str(e)
    
    return config_status


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
        from app.api.campaign_filter import get_allowed_campaign_ids
        from app.config import settings
        
        # If specific campaign IDs are configured, fetch them directly
        allowed_ids = get_allowed_campaign_ids()
        campaigns = []
        
        if allowed_ids:
            # Fetch configured campaigns directly by ID
            logger.info(f"Fetching configured Editorial Digest campaigns by ID: {allowed_ids}")
            for campaign_id in allowed_ids:
                try:
                    campaign = await service.get_campaign_by_id(campaign_id)
                    campaigns.append(campaign)
                    logger.debug(f"Successfully fetched campaign {campaign_id}: {campaign.get('name', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to fetch campaign {campaign_id}: {str(e)}")
                    # Continue with other campaigns even if one fails
        else:
            # No specific IDs configured, fetch from list and filter by name pattern
            campaigns = await service.get_campaigns(limit=limit, offset=offset)
            from app.api.campaign_filter import filter_campaigns
            campaigns = filter_campaigns(campaigns)
        
        # Validate and clean campaign data before creating Pydantic models
        validated_campaigns = []
        for c in campaigns:
            # Ensure all required string fields are not None - handle both dict.get() and direct access
            cleaned_campaign = {
                "id": str(c.get("id") or ""),
                "name": c.get("name") or "",
                "type": c.get("type") or "",
                "status": c.get("status") or "",
                "sendDate": c.get("sendDate") or "",
                "createdDate": c.get("createdDate") or "",
                "totalSends": int(c.get("totalSends", 0) or 0),
                "totalRecipients": int(c.get("totalRecipients", 0) or 0),
                "opens": int(c.get("opens", 0) or 0),
                "uniqueOpens": int(c.get("uniqueOpens", 0) or 0),
                "clicks": int(c.get("clicks", 0) or 0),
                "uniqueClicks": int(c.get("uniqueClicks", 0) or 0),
                "subscriberClicks": int(c.get("subscriberClicks", 0) or 0),
                "hardBounces": int(c.get("hardBounces", 0) or 0),
                "softBounces": int(c.get("softBounces", 0) or 0),
                "forwards": int(c.get("forwards", 0) or 0),
                "uniqueForwards": int(c.get("uniqueForwards", 0) or 0),
                "unsubscribes": int(c.get("unsubscribes", 0) or 0),
                "unsubReasons": int(c.get("unsubReasons", 0) or 0),
                "replies": int(c.get("replies", 0) or 0),
                "uniqueReplies": int(c.get("uniqueReplies", 0) or 0),
                "socialShares": int(c.get("socialShares", 0) or 0),
                "openRate": float(c.get("openRate", 0) or 0),
                "clickRate": float(c.get("clickRate", 0) or 0),
                "clickToOpenRate": float(c.get("clickToOpenRate", 0) or 0),
                "bounceRate": float(c.get("bounceRate", 0) or 0),
                "unsubscribeRate": float(c.get("unsubscribeRate", 0) or 0),
                "forwardRate": float(c.get("forwardRate", 0) or 0),
            }
            
            try:
                validated_campaigns.append(CampaignSummary(**cleaned_campaign))
            except Exception as validation_error:
                # Log the validation error but continue with other campaigns
                logger.warning(f"Failed to validate campaign {cleaned_campaign.get('id', 'unknown')}: {validation_error}")
                continue
        
        return CampaignsResponse(
            campaigns=validated_campaigns,
            total=len(validated_campaigns)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        # Check if it's a Pydantic validation error
        error_str = str(e)
        if "validation error" in error_str.lower() or "pydantic" in error_str.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Analytics service not configured: Data validation failed. Please check ActiveCampaign API configuration and ensure API credentials are correct. Error: {error_str}"
            )
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
        # Check if this is an Editorial Digest campaign
        from app.api.campaign_filter import is_editorial_digest_campaign, get_allowed_campaign_ids
        from app.config import settings
        
        # First fetch the campaign to get its name for pattern matching
        service = get_analytics_service()
        logger.info(f"Fetching campaign report for ID: {campaign_id}")
        
        try:
            campaign = await service.get_campaign_by_id(campaign_id)
            campaign_name = campaign.get("name", "")
            logger.info(f"Successfully fetched campaign {campaign_id}: {campaign_name}")
        except Exception as api_error:
            error_str = str(api_error)
            logger.error(
                f"Failed to fetch campaign {campaign_id} from ActiveCampaign API: {error_str}",
                exc_info=True
            )
            
            # Provide detailed error message
            if "404" in error_str or "not found" in error_str.lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"Campaign {campaign_id} not found in ActiveCampaign. Error: {error_str}"
                )
            elif "401" in error_str or "403" in error_str or "unauthorized" in error_str.lower():
                raise HTTPException(
                    status_code=503,
                    detail=f"ActiveCampaign authentication failed. Please check your API credentials. Error: {error_str}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch campaign from ActiveCampaign API: {error_str}"
                )
        
        if not is_editorial_digest_campaign(campaign_id, campaign_name):
            allowed_ids = get_allowed_campaign_ids()
            name_pattern = settings.EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN
            error_msg = f"Campaign {campaign_id} ('{campaign_name}') not found or not accessible. Only Editorial Digest campaigns are available."
            if allowed_ids:
                error_msg += f" Allowed IDs: {', '.join(allowed_ids)}"
            if name_pattern:
                error_msg += f" Name pattern: '{name_pattern}'"
            logger.warning(f"Campaign {campaign_id} ({campaign_name}) is not an Editorial Digest campaign")
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Ensure all required string fields are not None
        if campaign.get("sendDate") is None:
            campaign["sendDate"] = ""
        if campaign.get("createdDate") is None:
            campaign["createdDate"] = ""
        if campaign.get("id") is None:
            campaign["id"] = ""
        if campaign.get("name") is None:
            campaign["name"] = ""
        if campaign.get("type") is None:
            campaign["type"] = ""
        if campaign.get("status") is None:
            campaign["status"] = ""
        if campaign.get("subject") is None:
            campaign["subject"] = ""
        
        return CampaignReportResponse(
            campaign=CampaignReport(**campaign)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error(f"Analytics service configuration error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching campaign report for {campaign_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign report: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/test")
async def test_campaign_fetch(campaign_id: str):
    """
    Diagnostic endpoint to test fetching a specific campaign from ActiveCampaign.
    Returns detailed information about the API call including errors.
    
    Path params:
        campaign_id: Campaign ID to test
    
    Returns:
        Detailed diagnostic information about the API call
    """
    from app.config import settings
    from app.api.campaign_filter import is_editorial_digest_campaign, get_allowed_campaign_ids
    
    diagnostic_info = {
        "campaign_id": campaign_id,
        "base_url": settings.ACTIVECAMPAIGN_URL,
        "api_url": f"{settings.ACTIVECAMPAIGN_URL.rstrip('/')}/api/3/campaigns/{campaign_id}",
        "has_api_key": bool(settings.ACTIVECAMPAIGN_API_KEY and settings.ACTIVECAMPAIGN_API_KEY.strip()),
        "editorial_digest_allowed_ids": get_allowed_campaign_ids(),
        "editorial_digest_name_pattern": settings.EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN,
    }
    
    try:
        service = get_analytics_service()
        logger.info(f"Testing campaign fetch for ID: {campaign_id}")
        
        try:
            campaign = await service.get_campaign_by_id(campaign_id)
            diagnostic_info["api_call_success"] = True
            diagnostic_info["campaign_found"] = True
            diagnostic_info["campaign_name"] = campaign.get("name", "")
            diagnostic_info["campaign_status"] = campaign.get("status", "")
            diagnostic_info["campaign_send_date"] = campaign.get("sendDate", "")
            
            # Check if it's an Editorial Digest campaign
            campaign_name = campaign.get("name", "")
            is_editorial = is_editorial_digest_campaign(campaign_id, campaign_name)
            diagnostic_info["is_editorial_digest_campaign"] = is_editorial
            
            if not is_editorial:
                diagnostic_info["filter_reason"] = "Campaign does not match Editorial Digest filter criteria"
            
        except Exception as api_error:
            error_str = str(api_error)
            diagnostic_info["api_call_success"] = False
            diagnostic_info["campaign_found"] = False
            diagnostic_info["error"] = error_str
            diagnostic_info["error_type"] = type(api_error).__name__
            
            # Extract HTTP status if available
            if "HTTP" in error_str:
                try:
                    http_status = error_str.split("HTTP ")[-1].split()[0]
                    diagnostic_info["http_status"] = int(http_status)
                except:
                    pass
            
            logger.error(f"Campaign {campaign_id} test failed: {error_str}")
        
        return diagnostic_info
        
    except ValueError as e:
        diagnostic_info["service_initialization_error"] = str(e)
        diagnostic_info["api_call_success"] = False
        return diagnostic_info
    except Exception as e:
        diagnostic_info["unexpected_error"] = str(e)
        diagnostic_info["api_call_success"] = False
        logger.error(f"Unexpected error in test endpoint: {str(e)}", exc_info=True)
        return diagnostic_info


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
        # Check if this is an Editorial Digest campaign
        from app.api.campaign_filter import is_editorial_digest_campaign, get_allowed_campaign_ids
        from app.config import settings
        
        # First fetch the campaign to get its name for pattern matching
        service = get_analytics_service()
        logger.info(f"Fetching campaign links for ID: {campaign_id}")
        
        try:
            campaign = await service.get_campaign_by_id(campaign_id)
            campaign_name = campaign.get("name", "")
        except Exception as api_error:
            error_str = str(api_error)
            logger.error(f"Failed to fetch campaign {campaign_id} for links: {error_str}")
            if "404" in error_str or "not found" in error_str.lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"Campaign {campaign_id} not found in ActiveCampaign. Error: {error_str}"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch campaign from ActiveCampaign API: {error_str}"
            )
        
        if not is_editorial_digest_campaign(campaign_id, campaign_name):
            allowed_ids = get_allowed_campaign_ids()
            name_pattern = settings.EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN
            error_msg = f"Campaign {campaign_id} ('{campaign_name}') not found or not accessible. Only Editorial Digest campaigns are available."
            if allowed_ids:
                error_msg += f" Allowed IDs: {', '.join(allowed_ids)}"
            if name_pattern:
                error_msg += f" Name pattern: '{name_pattern}'"
            raise HTTPException(status_code=404, detail=error_msg)
        
        links = await service.get_campaign_links(campaign_id)
        
        return LinksResponse(
            links=[LinkData(**l) for l in links]
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error(f"Analytics service configuration error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service not configured: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to fetch campaign links for {campaign_id}: {str(e)}", exc_info=True)
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

"""
ActiveCampaign API Routes
Endpoints for integrating with ActiveCampaign for newsletter campaigns
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.activecampaign_service import get_activecampaign_service

router = APIRouter()


# Response Models
class ACList(BaseModel):
    """Subscriber list from ActiveCampaign"""
    id: str
    name: str
    subscriberCount: int = 0


class ACAddress(BaseModel):
    """Mailing address from ActiveCampaign"""
    id: str
    companyName: str
    display: str


class ListsResponse(BaseModel):
    """Response for lists endpoint"""
    lists: List[ACList]


class AddressesResponse(BaseModel):
    """Response for addresses endpoint"""
    addresses: List[ACAddress]


class PushCampaignRequest(BaseModel):
    """Request model for pushing a campaign"""
    listId: str
    campaignName: str
    subject: str
    htmlContent: str
    campaignStatus: str = "immediate"  # 'draft', 'scheduled', or 'immediate'
    addressId: Optional[str] = None
    scheduledDate: Optional[str] = None  # ISO format datetime
    senderName: Optional[str] = None
    senderEmail: Optional[str] = None


class PushCampaignResponse(BaseModel):
    """Response model for push campaign endpoint"""
    success: bool
    campaignId: str
    status: str
    message: str


@router.get("/lists", response_model=ListsResponse)
async def get_lists():
    """
    Fetch all subscriber lists from ActiveCampaign
    
    Returns:
        ListsResponse with array of lists containing id and name
    """
    try:
        service = get_activecampaign_service()
        lists_data = await service.get_lists()
        
        # Transform to match frontend expectations
        lists = [
            ACList(
                id=str(list_item.get("id", "")), 
                name=list_item.get("name", ""),
                subscriberCount=list_item.get("subscriber_count", 0)
            )
            for list_item in lists_data
        ]
        
        return ListsResponse(lists=lists)
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ActiveCampaign service not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch ActiveCampaign lists: {str(e)}"
        )


@router.get("/addresses", response_model=AddressesResponse)
async def get_addresses():
    """
    Fetch all mailing addresses from ActiveCampaign
    
    Returns:
        AddressesResponse with array of addresses containing id, companyName, and display
    """
    try:
        service = get_activecampaign_service()
        addresses_data = await service.get_addresses()
        
        # Transform to match frontend expectations
        addresses = [
            ACAddress(
                id=str(addr.get("id", "")),
                companyName=addr.get("companyName", ""),
                display=addr.get("display", "")
            )
            for addr in addresses_data
        ]
        
        return AddressesResponse(addresses=addresses)
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ActiveCampaign service not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch ActiveCampaign addresses: {str(e)}"
        )


@router.post("/push", response_model=PushCampaignResponse)
async def push_campaign(request: PushCampaignRequest):
    """
    Create and send a newsletter campaign to ActiveCampaign
    
    This endpoint:
    1. Creates an email message with the provided HTML content (v3 API)
    2. Creates a campaign linked to the specified list (v1 API)
    
    Args:
        request: PushCampaignRequest with campaign details
    
    Returns:
        PushCampaignResponse with campaign ID and status
    """
    try:
        service = get_activecampaign_service()
        
        # Validate scheduled date if status is scheduled
        if request.campaignStatus == "scheduled" and not request.scheduledDate:
            raise HTTPException(
                status_code=422,
                detail="scheduledDate is required when campaignStatus is 'scheduled'"
            )
        
        # Push the newsletter using the service
        result = await service.push_newsletter(
            list_id=request.listId,
            campaign_name=request.campaignName,
            subject=request.subject,
            html_content=request.htmlContent,
            campaign_status=request.campaignStatus,
            address_id=request.addressId,
            scheduled_date=request.scheduledDate,
            sender_name=request.senderName,
            sender_email=request.senderEmail
        )
        
        # Determine success message based on status
        status_messages = {
            "draft": "Campaign created as draft",
            "scheduled": "Campaign scheduled successfully",
            "immediate": "Campaign created and sent successfully"
        }
        message = status_messages.get(result["status"], "Campaign created successfully")
        
        return PushCampaignResponse(
            success=True,
            campaignId=str(result["campaign_id"]),
            status=result["status"],
            message=message
        )
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ActiveCampaign service not configured: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to push campaign to ActiveCampaign: {str(e)}"
        )

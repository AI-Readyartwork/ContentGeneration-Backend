"""
ActiveCampaign Analytics Service

Handles campaign analytics and reporting API calls:
- Campaign list with performance metrics
- Detailed campaign reports
- Link click tracking data
"""

import httpx
from typing import Optional, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for ActiveCampaign analytics."""
    
    def __init__(self):
        self.base_url = settings.ACTIVECAMPAIGN_URL
        self.api_key = settings.ACTIVECAMPAIGN_API_KEY
        
        # Check if URL and API key are configured (not None and not empty string)
        if not self.base_url or not self.api_key or self.base_url.strip() == "" or self.api_key.strip() == "":
            raise ValueError("ActiveCampaign URL and API Key must be configured. Please set ACTIVECAMPAIGN_URL and ACTIVECAMPAIGN_API_KEY environment variables.")
        
        self.base_url = self.base_url.rstrip('/')
        
        self.headers = {
            "Api-Token": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _handle_response(self, response, operation_name: str, request_url: str = "") -> dict:
        """Handle API response and raise descriptive errors."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    error_msg = str(error_data['errors'])
                elif 'message' in error_data:
                    error_msg = error_data['message']
                else:
                    error_msg = str(error_data)
            except:
                error_msg = response.text or f"HTTP {response.status_code}"
            
            # Log detailed error information
            logger.error(
                f"{operation_name} failed: {error_msg} (HTTP {response.status_code})"
                + (f" | URL: {request_url}" if request_url else "")
                + f" | Response: {response.text[:500] if response.text else 'No response body'}"
            )
            
            raise Exception(f"{operation_name} failed: {error_msg} (HTTP {response.status_code})")
        
        return response.json()
    
    async def get_campaigns(self, limit: int = 500, offset: int = 0) -> List[dict]:
        """
        Fetch all campaigns with their performance metrics.
        
        Returns:
            List of campaign objects with stats
        """
        # Double-check configuration before making API call
        if not self.base_url or not self.api_key or not self.base_url.strip() or not self.api_key.strip():
            raise ValueError("ActiveCampaign URL and API Key must be configured. Please set ACTIVECAMPAIGN_URL and ACTIVECAMPAIGN_API_KEY environment variables.")
        
        async with httpx.AsyncClient() as client:
            try:
                request_url = f"{self.base_url}/api/3/campaigns"
                logger.debug(f"Fetching campaigns: URL={request_url}, limit={limit}, offset={offset}")
                response = await client.get(
                    request_url,
                    headers=self.headers,
                    params={"limit": limit, "offset": offset},
                    timeout=30.0
                )
                data = self._handle_response(response, "Get campaigns", request_url)
            except Exception as e:
                # If API call fails, it might be due to invalid credentials
                error_msg = str(e)
                if "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg:
                    raise ValueError(f"ActiveCampaign authentication failed. Please check your API credentials. Error: {error_msg}")
                raise ValueError(f"Failed to connect to ActiveCampaign API. Please verify ACTIVECAMPAIGN_URL is correct. Error: {error_msg}")
            
            campaigns = []
            for campaign in data.get("campaigns", []):
                # Parse campaign data with all metrics
                # Ensure all string fields handle None values
                sdate = campaign.get("sdate") or ""
                cdate = campaign.get("cdate") or ""
                campaigns.append({
                    "id": str(campaign.get("id", "")),
                    "name": campaign.get("name") or "",
                    "type": campaign.get("type") or "",
                    "status": self._get_status_label(campaign.get("status", "0")),
                    "sendDate": sdate,
                    "createdDate": cdate,
                    
                    # Core metrics
                    "totalSends": int(campaign.get("send_amt", 0) or 0),
                    "totalRecipients": int(campaign.get("total_amt", 0) or 0),
                    
                    # Engagement metrics
                    "opens": int(campaign.get("opens", 0) or 0),
                    "uniqueOpens": int(campaign.get("uniqueopens", 0) or 0),
                    "clicks": int(campaign.get("linkclicks", 0) or 0),
                    "uniqueClicks": int(campaign.get("uniquelinkclicks", 0) or 0),
                    "subscriberClicks": int(campaign.get("subscriberclicks", 0) or 0),
                    
                    # Deliverability metrics
                    "hardBounces": int(campaign.get("hardbounces", 0) or 0),
                    "softBounces": int(campaign.get("softbounces", 0) or 0),
                    "forwards": int(campaign.get("forwards", 0) or 0),
                    "uniqueForwards": int(campaign.get("uniqueforwards", 0) or 0),
                    
                    # Subscription metrics
                    "unsubscribes": int(campaign.get("unsubscribes", 0) or 0),
                    "unsubReasons": int(campaign.get("unsubreasons", 0) or 0),
                    "replies": int(campaign.get("replies", 0) or 0),
                    "uniqueReplies": int(campaign.get("uniquereplies", 0) or 0),
                    
                    # Social metrics
                    "socialShares": int(campaign.get("socialshares", 0) or 0),
                    
                    # Calculated rates (percentage)
                    "openRate": self._calc_rate(campaign.get("uniqueopens"), campaign.get("send_amt")),
                    "clickRate": self._calc_rate(campaign.get("uniquelinkclicks"), campaign.get("send_amt")),
                    "clickToOpenRate": self._calc_rate(campaign.get("uniquelinkclicks"), campaign.get("uniqueopens")),
                    "bounceRate": self._calc_rate(
                        int(campaign.get("hardbounces", 0) or 0) + int(campaign.get("softbounces", 0) or 0),
                        campaign.get("send_amt")
                    ),
                    "unsubscribeRate": self._calc_rate(campaign.get("unsubscribes"), campaign.get("send_amt")),
                    "forwardRate": self._calc_rate(campaign.get("uniqueforwards"), campaign.get("send_amt")),
                })
            
            return campaigns
    
    async def get_campaign_by_id(self, campaign_id: str) -> dict:
        """
        Get detailed campaign information by ID.
        
        Returns:
            Campaign object with full metrics
        """
        async with httpx.AsyncClient() as client:
            request_url = f"{self.base_url}/api/3/campaigns/{campaign_id}"
            logger.info(f"Fetching campaign by ID: {campaign_id} | URL: {request_url}")
            try:
                response = await client.get(
                    request_url,
                    headers=self.headers,
                    timeout=30.0
                )
                data = self._handle_response(response, "Get campaign", request_url)
            except Exception as e:
                logger.error(
                    f"Failed to fetch campaign {campaign_id}: {str(e)} | "
                    f"URL: {request_url} | "
                    f"Base URL: {self.base_url}"
                )
                raise
            
            campaign = data.get("campaign", {})
            
            # Ensure all string fields handle None values
            sdate = campaign.get("sdate") or ""
            cdate = campaign.get("cdate") or ""
            return {
                "id": str(campaign.get("id", "")),
                "name": campaign.get("name") or "",
                "type": campaign.get("type") or "",
                "status": self._get_status_label(campaign.get("status", "0")),
                "sendDate": sdate,
                "createdDate": cdate,
                "subject": campaign.get("subject") or "",
                
                # Core metrics
                "totalSends": int(campaign.get("send_amt", 0) or 0),
                "totalRecipients": int(campaign.get("total_amt", 0) or 0),
                
                # Engagement metrics
                "opens": int(campaign.get("opens", 0) or 0),
                "uniqueOpens": int(campaign.get("uniqueopens", 0) or 0),
                "clicks": int(campaign.get("linkclicks", 0) or 0),
                "uniqueClicks": int(campaign.get("uniquelinkclicks", 0) or 0),
                "subscriberClicks": int(campaign.get("subscriberclicks", 0) or 0),
                
                # Deliverability metrics
                "hardBounces": int(campaign.get("hardbounces", 0) or 0),
                "softBounces": int(campaign.get("softbounces", 0) or 0),
                "forwards": int(campaign.get("forwards", 0) or 0),
                "uniqueForwards": int(campaign.get("uniqueforwards", 0) or 0),
                
                # Subscription metrics
                "unsubscribes": int(campaign.get("unsubscribes", 0) or 0),
                "unsubReasons": int(campaign.get("unsubreasons", 0) or 0),
                "replies": int(campaign.get("replies", 0) or 0),
                "uniqueReplies": int(campaign.get("uniquereplies", 0) or 0),
                
                # Social metrics
                "socialShares": int(campaign.get("socialshares", 0) or 0),
                
                # Calculated rates
                "openRate": self._calc_rate(campaign.get("uniqueopens"), campaign.get("send_amt")),
                "clickRate": self._calc_rate(campaign.get("uniquelinkclicks"), campaign.get("send_amt")),
                "clickToOpenRate": self._calc_rate(campaign.get("uniquelinkclicks"), campaign.get("uniqueopens")),
                "bounceRate": self._calc_rate(
                    int(campaign.get("hardbounces", 0) or 0) + int(campaign.get("softbounces", 0) or 0),
                    campaign.get("send_amt")
                ),
                "unsubscribeRate": self._calc_rate(campaign.get("unsubscribes"), campaign.get("send_amt")),
                "forwardRate": self._calc_rate(campaign.get("uniqueforwards"), campaign.get("send_amt")),
            }
    
    async def get_campaign_links(self, campaign_id: str) -> List[dict]:
        """
        Get click tracking data for campaign links.
        
        Returns:
            List of link objects with click counts
        """
        async with httpx.AsyncClient() as client:
            request_url = f"{self.base_url}/api/3/campaigns/{campaign_id}/links"
            response = await client.get(
                request_url,
                headers=self.headers,
                timeout=30.0
            )
            data = self._handle_response(response, "Get campaign links", request_url)
            
            links = []
            for link in data.get("links", []):
                links.append({
                    "id": link.get("id"),
                    "url": link.get("link", ""),
                    "name": link.get("name", ""),
                    "clicks": int(link.get("clicks", 0) or 0),
                    "uniqueClicks": int(link.get("uniqueclicks", 0) or 0),
                })
            
            # Sort by clicks descending
            links.sort(key=lambda x: x["clicks"], reverse=True)
            
            return links
    
    async def get_lists_with_counts(self) -> List[dict]:
        """
        Get all subscriber lists with contact counts.
        
        Returns:
            List of lists with subscriber counts
        """
        async with httpx.AsyncClient() as client:
            request_url = f"{self.base_url}/api/3/lists"
            response = await client.get(
                request_url,
                headers=self.headers,
                timeout=30.0
            )
            data = self._handle_response(response, "Get lists", request_url)
            
            lists = []
            for lst in data.get("lists", []):
                lists.append({
                    "id": lst.get("id"),
                    "name": lst.get("name", ""),
                    "subscriberCount": int(lst.get("subscriber_count", 0) or 0),
                })
            
            return lists
    
    def _get_status_label(self, status: str) -> str:
        """Convert status code to human-readable label."""
        status_map = {
            "0": "Draft",
            "1": "Scheduled",
            "2": "Sending",
            "3": "Paused",
            "4": "Stopped",
            "5": "Completed"
        }
        return status_map.get(str(status), "Unknown")
    
    def _calc_rate(self, numerator, denominator) -> float:
        """Calculate percentage rate safely."""
        try:
            num = int(numerator or 0)
            denom = int(denominator or 0)
            if denom == 0:
                return 0.0
            return round((num / denom) * 100, 2)
        except:
            return 0.0


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service

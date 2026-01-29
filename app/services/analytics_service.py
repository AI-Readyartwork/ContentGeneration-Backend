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
        
        if not self.base_url or not self.api_key:
            raise ValueError("ActiveCampaign URL and API Key must be configured")
        
        self.base_url = self.base_url.rstrip('/')
        
        self.headers = {
            "Api-Token": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _handle_response(self, response, operation_name: str) -> dict:
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
            
            raise Exception(f"{operation_name} failed: {error_msg} (HTTP {response.status_code})")
        
        return response.json()
    
    async def get_campaigns(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """
        Fetch all campaigns with their performance metrics.
        
        Returns:
            List of campaign objects with stats
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/3/campaigns",
                headers=self.headers,
                params={"limit": limit, "offset": offset},
                timeout=30.0
            )
            data = self._handle_response(response, "Get campaigns")
            
            campaigns = []
            for campaign in data.get("campaigns", []):
                # Parse campaign data with all metrics
                campaigns.append({
                    "id": campaign.get("id"),
                    "name": campaign.get("name", ""),
                    "type": campaign.get("type", ""),
                    "status": self._get_status_label(campaign.get("status", "0")),
                    "sendDate": campaign.get("sdate", ""),
                    "createdDate": campaign.get("cdate", ""),
                    
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
            response = await client.get(
                f"{self.base_url}/api/3/campaigns/{campaign_id}",
                headers=self.headers,
                timeout=30.0
            )
            data = self._handle_response(response, "Get campaign")
            
            campaign = data.get("campaign", {})
            
            return {
                "id": campaign.get("id"),
                "name": campaign.get("name", ""),
                "type": campaign.get("type", ""),
                "status": self._get_status_label(campaign.get("status", "0")),
                "sendDate": campaign.get("sdate", ""),
                "createdDate": campaign.get("cdate", ""),
                "subject": campaign.get("subject", ""),
                
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
            response = await client.get(
                f"{self.base_url}/api/3/campaigns/{campaign_id}/links",
                headers=self.headers,
                timeout=30.0
            )
            data = self._handle_response(response, "Get campaign links")
            
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
            response = await client.get(
                f"{self.base_url}/api/3/lists",
                headers=self.headers,
                timeout=30.0
            )
            data = self._handle_response(response, "Get lists")
            
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

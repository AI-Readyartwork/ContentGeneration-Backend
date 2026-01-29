"""
Utility functions for filtering Editorial Digest campaigns.
Centralized logic to ensure consistent ID comparison across all endpoints.
"""
from app.config import settings


def is_editorial_digest_campaign(campaign_id: str, campaign_name: str = "") -> bool:
    """
    Check if a campaign ID belongs to Editorial Digest campaigns.
    Can also match by name pattern if configured.
    
    Args:
        campaign_id: Campaign ID (can be string or will be converted)
        campaign_name: Optional campaign name for pattern matching
    
    Returns:
        True if the campaign is an Editorial Digest campaign, False otherwise
    """
    allowed_ids = settings.editorial_digest_campaign_ids
    name_pattern = settings.EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN
    
    # If neither IDs nor pattern configured, allow all (backward compatibility)
    if not allowed_ids and not name_pattern:
        return True
    
    # Check by ID
    if allowed_ids:
        allowed_ids_set = {str(aid).strip() for aid in allowed_ids}
        campaign_id_normalized = str(campaign_id).strip()
        if campaign_id_normalized in allowed_ids_set:
            return True
    
    # Check by name pattern
    if name_pattern and campaign_name:
        pattern_lower = name_pattern.lower().strip()
        name_lower = campaign_name.lower()
        if pattern_lower in name_lower:
            return True
    
    return False


def get_allowed_campaign_ids() -> list[str]:
    """
    Get the list of allowed Editorial Digest campaign IDs.
    
    Returns:
        List of campaign ID strings
    """
    return settings.editorial_digest_campaign_ids


def filter_campaigns(campaigns: list[dict]) -> list[dict]:
    """
    Filter a list of campaigns to only include Editorial Digest campaigns.
    Can match by ID or by name pattern.
    
    Args:
        campaigns: List of campaign dictionaries with 'id' and optionally 'name' fields
    
    Returns:
        Filtered list containing only Editorial Digest campaigns
    """
    allowed_ids = settings.editorial_digest_campaign_ids
    name_pattern = settings.EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN
    
    # If neither IDs nor pattern configured, return all campaigns
    if not allowed_ids and not name_pattern:
        return campaigns
    
    # Normalize allowed IDs to a set for O(1) lookup
    allowed_ids_set = None
    if allowed_ids:
        allowed_ids_set = {str(aid).strip() for aid in allowed_ids}
    
    # Normalize name pattern
    pattern_lower = None
    if name_pattern:
        pattern_lower = name_pattern.lower().strip()
    
    # Filter campaigns
    filtered = []
    for campaign in campaigns:
        campaign_id = str(campaign.get("id", "")).strip()
        campaign_name = campaign.get("name", "")
        
        # Check by ID
        if allowed_ids_set and campaign_id in allowed_ids_set:
            filtered.append(campaign)
            continue
        
        # Check by name pattern
        if pattern_lower and campaign_name:
            if pattern_lower in campaign_name.lower():
                filtered.append(campaign)
    
    return filtered

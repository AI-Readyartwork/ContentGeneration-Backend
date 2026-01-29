from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # OpenRouter (for Perplexity Sonar Pro)
    OPENROUTER_API_KEY: str = ""
    
    # Giphy API
    GIPHY_API_KEY: str = ""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # ActiveCampaign
    ACTIVECAMPAIGN_URL: str = ""
    ACTIVECAMPAIGN_API_KEY: str = ""
    ACTIVECAMPAIGN_SENDER_NAME: str = "Ready Artwork"
    ACTIVECAMPAIGN_SENDER_EMAIL: str = "ai@readyartwork.com"
    
    # Editorial Digest Campaign IDs (comma-separated, e.g., "330,329")
    # Only campaigns with these IDs will be shown in analytics dashboard
    # Leave empty to auto-detect by name pattern
    EDITORIAL_DIGEST_CAMPAIGN_IDS: str = "330,329"
    
    # Editorial Digest Campaign Name Pattern (optional)
    # If set, campaigns matching this pattern will be included (in addition to IDs)
    # Example: "Weekly Newsletter" will match "Weekly Newsletter 28 January 2026"
    EDITORIAL_DIGEST_CAMPAIGN_NAME_PATTERN: str = ""
    
    # n8n Webhook (optional - for triggering n8n workflows)
    N8N_NEWS_WEBHOOK: str = ""
    
    # CORS - comma-separated string
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def editorial_digest_campaign_ids(self) -> List[str]:
        """Convert EDITORIAL_DIGEST_CAMPAIGN_IDS string to list of campaign IDs"""
        if not self.EDITORIAL_DIGEST_CAMPAIGN_IDS:
            return []
        return [cid.strip() for cid in self.EDITORIAL_DIGEST_CAMPAIGN_IDS.split(",") if cid.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

"""
Scheduler service for automatic news updates every 24 hours at midnight
"""
import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx

from app.config import settings

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def update_all_pillars_news():
    """
    Fetch and update news for all pillars in the database.
    This function runs automatically at midnight every day.
    """
    print(f"\n{'='*60}")
    print(f"[SCHEDULER] Starting daily news update at {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            print("[SCHEDULER] ERROR: Supabase credentials not configured")
            return
        
        # Create Supabase client
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Fetch all pillars
        result = supabase.table("pillars").select("id, name, keywords").execute()
        pillars = result.data
        
        if not pillars:
            print("[SCHEDULER] No pillars found to update")
            return
        
        print(f"[SCHEDULER] Found {len(pillars)} pillars to update")
        
        # Import news service
        from app.services.news_service import NewsService
        news_service = NewsService()
        
        success_count = 0
        fail_count = 0
        
        for pillar in pillars:
            try:
                pillar_name = pillar.get("name", "Unknown")
                pillar_id = pillar.get("id")
                keywords = pillar.get("keywords", [])
                
                print(f"\n[SCHEDULER] Updating pillar: {pillar_name}")
                
                # Map pillar name to category
                category = pillar_name.lower().replace(" ", "_")
                
                # Fetch fresh news for this pillar
                news_items = await news_service.fetch_news_with_catchy_titles(
                    category=category,
                    num_items=6
                )
                
                if news_items:
                    # Convert news items to dict format for storage
                    news_data = [
                        {
                            "id": item.id,
                            "category": item.category,
                            "title": item.title,
                            "publisher": item.publisher,
                            "published_date": item.published_date,
                            "url": item.url,
                            "summary": item.summary,
                            "why_it_matters": item.why_it_matters,
                            "action_items": item.action_items,
                            "tags": item.tags,
                        }
                        for item in news_items
                    ]
                    
                    # Update pillar with new news
                    update_result = supabase.table("pillars").update({
                        "news_items": news_data,
                        "last_updated": datetime.now().isoformat()
                    }).eq("id", pillar_id).execute()
                    
                    print(f"[SCHEDULER] ✓ Updated {pillar_name} with {len(news_items)} news items")
                    success_count += 1
                else:
                    print(f"[SCHEDULER] ⚠ No news found for {pillar_name}")
                    fail_count += 1
                    
                # Small delay between pillars to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[SCHEDULER] ✗ Error updating {pillar.get('name', 'Unknown')}: {str(e)}")
                fail_count += 1
        
        # Log completion
        print(f"\n{'='*60}")
        print(f"[SCHEDULER] Daily news update completed at {datetime.now().isoformat()}")
        print(f"[SCHEDULER] Results: {success_count} success, {fail_count} failed")
        print(f"{'='*60}\n")
        
        # Optionally log to cron_jobs table
        try:
            supabase.table("cron_jobs").insert({
                "job_name": "daily-news-update",
                "status": "success" if fail_count == 0 else "partial",
                "results": {
                    "total_pillars": len(pillars),
                    "success": success_count,
                    "failed": fail_count
                }
            }).execute()
        except Exception as e:
            print(f"[SCHEDULER] Could not log to cron_jobs table: {e}")
            
    except Exception as e:
        print(f"[SCHEDULER] ERROR: Failed to update news: {str(e)}")
        import traceback
        traceback.print_exc()


async def trigger_n8n_workflow():
    """
    Alternative: Trigger n8n workflow for news updates.
    Use this if you prefer n8n to handle the actual news fetching.
    """
    print(f"[SCHEDULER] Triggering n8n workflow at {datetime.now().isoformat()}")
    
    n8n_webhook_url = getattr(settings, 'N8N_NEWS_WEBHOOK', None)
    
    if not n8n_webhook_url:
        print("[SCHEDULER] N8N_NEWS_WEBHOOK not configured, using direct update instead")
        await update_all_pillars_news()
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                n8n_webhook_url,
                json={
                    "trigger": "scheduled",
                    "timestamp": datetime.now().isoformat(),
                    "source": "backend-scheduler"
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                print(f"[SCHEDULER] ✓ n8n workflow triggered successfully")
            else:
                print(f"[SCHEDULER] ✗ n8n workflow failed: {response.status_code}")
                # Fallback to direct update
                await update_all_pillars_news()
                
    except Exception as e:
        print(f"[SCHEDULER] ✗ Error triggering n8n: {str(e)}")
        # Fallback to direct update
        await update_all_pillars_news()


def start_scheduler():
    """
    Initialize and start the APScheduler.
    Schedules the news update job to run daily at midnight (00:00).
    """
    global scheduler
    
    if scheduler is not None:
        print("[SCHEDULER] Scheduler already running")
        return scheduler
    
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    # Schedule job to run daily at midnight (00:00 UTC)
    # CronTrigger: minute=0, hour=0 means 00:00 every day
    scheduler.add_job(
        update_all_pillars_news,
        trigger=CronTrigger(hour=0, minute=0),  # Every day at 00:00 UTC
        id="daily_news_update",
        name="Daily News Update",
        replace_existing=True,
        misfire_grace_time=3600  # Allow 1 hour grace period if missed
    )
    
    # Start the scheduler
    scheduler.start()
    
    # Get next run time
    job = scheduler.get_job("daily_news_update")
    next_run = job.next_run_time if job else "Unknown"
    
    print(f"\n{'='*60}")
    print("[SCHEDULER] Automatic news update scheduler started!")
    print(f"[SCHEDULER] Schedule: Every day at 00:00 UTC (midnight)")
    print(f"[SCHEDULER] Next scheduled run: {next_run}")
    print(f"{'='*60}\n")
    
    return scheduler


def stop_scheduler():
    """Stop the scheduler gracefully"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        print("[SCHEDULER] Scheduler stopped")


def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    
    if not scheduler:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }


async def run_news_update_now():
    """
    Manually trigger news update (for testing or admin use).
    """
    print("[SCHEDULER] Manual news update triggered")
    await update_all_pillars_news()

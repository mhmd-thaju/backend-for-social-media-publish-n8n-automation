import asyncio
import httpx
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from typing import Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://testingautomations.app.n8n.cloud/webhook-test/fastapi-data")


async def init_scheduler():
    """Initialize the APScheduler scheduler"""
    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("✓ Scheduler initialized")
    return scheduler


async def get_scheduler() -> AsyncIOScheduler:
    """Get or initialize the scheduler"""
    global scheduler
    if scheduler is None:
        await init_scheduler()
    return scheduler


async def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("✓ Scheduler shutdown")


async def schedule_workflow(
    scheduled_time: datetime,
    payload: dict,
    post_id: str
):
    """
    Schedule a workflow to execute at a specific time.
    
    Args:
        scheduled_time: When to execute the workflow
        payload: Data to send to n8n
        post_id: Database ID of the post for reference
    """
    sched = await get_scheduler()
    
    try:
        job = sched.add_job(
            execute_workflow,
            DateTrigger(run_date=scheduled_time),
            args=[payload, post_id],
            id=f"post_{post_id}",
            replace_existing=True
        )
        logger.info(f"✓ Scheduled job {post_id} for {scheduled_time}")
        return job.id
    except Exception as e:
        logger.error(f"✗ Failed to schedule job {post_id}: {str(e)}")
        raise


async def execute_workflow(payload: dict, post_id: str):
    """
    Execute the n8n workflow at scheduled time.
    
    Args:
        payload: Data to send to n8n
        post_id: Database ID of the post
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=15.0
            )
            response.raise_for_status()
            logger.info(f"✓ Workflow executed for post {post_id}")
            
            # Update post status in database (within the async context)
            from database import get_async_db
            from bson import ObjectId
            db = await get_async_db()
            await db.scheduled_posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "status": "published",
                        "published_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"✓ Updated post {post_id} status to published")
            
    except Exception as e:
        logger.error(f"✗ Workflow execution failed for post {post_id}: {str(e)}")
        
        # Update post status with error
        try:
            from database import get_async_db
            from bson import ObjectId
            db = await get_async_db()
            await db.scheduled_posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e)
                    }
                }
            )
        except Exception as db_error:
            logger.error(f"✗ Failed to update error status: {str(db_error)}")


async def cancel_scheduled_workflow(post_id: str):
    """Cancel a scheduled workflow"""
    sched = await get_scheduler()
    try:
        sched.remove_job(f"post_{post_id}")
        logger.info(f"✓ Cancelled scheduled workflow for {post_id}")
    except Exception as e:
        logger.error(f"✗ Failed to cancel job {post_id}: {str(e)}")

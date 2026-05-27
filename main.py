from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import logging
import os

from database import connect_to_mongo, close_mongo, get_async_db
from models import (
    ScheduledPost, PublishedPost, Account, 
    MediaTypeEnum, PlatformEnum, StatusEnum
)
from scheduler_queue import init_scheduler, shutdown_scheduler, schedule_workflow, cancel_scheduled_workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="n8n Social Media Bridge")

# Setup Jinja2 for the UI
templates = Jinja2Templates(directory="templates")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and scheduler on startup"""
    logger.info("🚀 Starting application...")
    await connect_to_mongo()
    await init_scheduler()
    logger.info("✓ Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down application...")
    await close_mongo()
    await shutdown_scheduler()
    logger.info("✓ Application shut down successfully")


# ============ DASHBOARD & UI ============

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Renders the main control panel UI."""
    return templates.TemplateResponse("index.html", {"request": request})


# ============ SOCIAL MEDIA PUBLISHING ============

@app.post("/api/publish")
async def handle_publish(
    media_type: str = Form(...), 
    platform: str = Form(...),
    scheduled_time: str = Form(...),    
    text_topic: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None)
):
    """Receives form data, saves to DB, and schedules workflow."""
    
    # Validation for unsupported media types on platforms
    if media_type == "text" and platform in ["instagram", "both", "linkedin"]:
        raise HTTPException(status_code=400, detail="Text posts are only supported on Facebook.")
    if media_type in ["story_image", "story_video"] and platform in ["facebook", "both", "linkedin"]:
        raise HTTPException(status_code=400, detail="Stories are only supported on Instagram.")
    if platform == "linkedin" and media_type not in ["linkedin_text", "linkedin_image"]:
        raise HTTPException(status_code=400, detail="LinkedIn only supports LinkedIn Text or LinkedIn Image posts.")
    if media_type in ["linkedin_text", "linkedin_image"] and platform != "linkedin":
        raise HTTPException(status_code=400, detail="LinkedIn media types are only supported on the LinkedIn platform.")
    
    # Parse scheduled time
    try:
        if scheduled_time.lower() == "immediate":
            sched_time = datetime.utcnow()
            is_immediate = True
        else:
            sched_time = datetime.fromisoformat(scheduled_time)
            is_immediate = False
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use YYYY-MM-DD HH:MM:SS")
    
    # Create post document
    post_data = ScheduledPost(
        media_type=media_type,
        platform=platform,
        scheduled_time=sched_time,
        text_topic=text_topic,
        image_url=image_url,
        video_url=video_url,
        status=StatusEnum.PENDING if is_immediate else StatusEnum.SCHEDULED
    )
    
    # Save to database
    db = await get_async_db()
    result = await db.scheduled_posts.insert_one(post_data.dict())
    post_id = str(result.inserted_id)
    logger.info(f"✓ Post saved to database: {post_id}")
    
    # Prepare payload for n8n
    payload = {
        "media_type": media_type,
        "platform": platform,
        "scheduled_time": sched_time.isoformat(),
        "text_topic": text_topic,
        "image_url": image_url,
        "video_url": video_url,
        "post_id": post_id
    }
    
    # Schedule or execute immediately
    try:
        if is_immediate:
            # Execute immediately
            from scheduler_queue import execute_workflow
            await execute_workflow(payload, post_id)
            return {
                "status": "ok",
                "message": "Post published immediately!",
                "post_id": post_id
            }
        else:
            # Schedule for later
            await schedule_workflow(sched_time, payload, post_id)
            return {
                "status": "ok",
                "message": f"Post scheduled for {sched_time.isoformat()}",
                "post_id": post_id
            }
    except Exception as e:
        logger.error(f"✗ Error processing post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============ ACCOUNTS MANAGEMENT ============

@app.get("/api/accounts")
async def get_accounts():
    """Fetch all saved accounts"""
    db = await get_async_db()
    accounts = await db.accounts.find().to_list(None)
    
    # Convert ObjectId to string for JSON serialization
    for acc in accounts:
        acc["_id"] = str(acc["_id"])
        if acc.get("token_expiry_date"):
            acc["token_expiry_date"] = acc["token_expiry_date"].isoformat()
        acc["created_at"] = acc["created_at"].isoformat()
    
    return accounts


@app.post("/api/accounts")
async def create_account(
    platform: str = Form(...),
    account_name: str = Form(...),
    page_access_token: Optional[str] = Form(None),
    user_access_token: Optional[str] = Form(None),
    token_expiry_date: Optional[str] = Form(None)
):
    """Create or update an account"""
    try:
        expiry_date = None
        if token_expiry_date:
            expiry_date = datetime.fromisoformat(token_expiry_date)
        
        account = Account(
            platform=platform,
            account_name=account_name,
            page_access_token=page_access_token,
            user_access_token=user_access_token,
            token_expiry_date=expiry_date
        )
        
        db = await get_async_db()
        result = await db.accounts.insert_one(account.dict())
        
        logger.info(f"✓ Account created: {account_name} ({platform})")
        return {
            "status": "ok",
            "account_id": str(result.inserted_id),
            "message": "Account saved successfully"
        }
    except Exception as e:
        logger.error(f"✗ Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str):
    """Delete an account"""
    try:
        db = await get_async_db()
        result = await db.accounts.delete_one({"_id": ObjectId(account_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        
        logger.info(f"✓ Account deleted: {account_id}")
        return {"status": "ok", "message": "Account deleted"}
    except Exception as e:
        logger.error(f"✗ Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/expiry-warnings")
async def get_expiry_warnings():
    """Get accounts with tokens expiring within 7 days"""
    db = await get_async_db()
    
    now = datetime.utcnow()
    week_later = now + timedelta(days=7)
    
    accounts = await db.accounts.find({
        "token_expiry_date": {
            "$gte": now,
            "$lte": week_later
        }
    }).to_list(None)
    
    for acc in accounts:
        acc["_id"] = str(acc["_id"])
        acc["token_expiry_date"] = acc["token_expiry_date"].isoformat()
    
    return accounts


# ============ POSTS MANAGEMENT ============

@app.get("/api/posts")
async def get_posts(status: Optional[str] = None):
    """Fetch scheduled and published posts"""
    db = await get_async_db()
    
    query = {}
    if status:
        query["status"] = status
    
    posts = await db.scheduled_posts.find(query).to_list(None)
    
    for post in posts:
        post["_id"] = str(post["_id"])
        post["scheduled_time"] = post["scheduled_time"].isoformat()
        post["created_at"] = post["created_at"].isoformat()
        if post.get("published_at"):
            post["published_at"] = post["published_at"].isoformat()
    
    return posts


@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str):
    """Delete a scheduled post"""
    try:
        db = await get_async_db()
        post = await db.scheduled_posts.find_one({"_id": ObjectId(post_id)})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Cancel scheduled workflow
        if post["status"] == "scheduled":
            await cancel_scheduled_workflow(post_id)
        
        # Delete from database
        await db.scheduled_posts.delete_one({"_id": ObjectId(post_id)})
        
        logger.info(f"✓ Post deleted: {post_id}")
        return {"status": "ok", "message": "Post deleted"}
    except Exception as e:
        logger.error(f"✗ Error deleting post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
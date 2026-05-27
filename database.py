from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import asyncio
from typing import Optional
import os
from datetime import datetime

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = "social_media_scheduler"

# Synchronous MongoDB client for initialization
sync_client: Optional[MongoClient] = None
sync_db = None

# Async MongoDB client
async_client: Optional[AsyncIOMotorClient] = None
async_db = None


async def connect_to_mongo():
    """Initialize MongoDB connection (async)"""
    global async_client, async_db
    async_client = AsyncIOMotorClient(MONGO_URL)
    async_db = async_client[DATABASE_NAME]
    
    # Create collections and indexes
    await async_db.scheduled_posts.create_index("scheduled_time")
    await async_db.scheduled_posts.create_index("status")
    await async_db.published_posts.create_index("published_at")
    await async_db.accounts.create_index("platform")
    await async_db.accounts.create_index("expiry_date")
    
    print("✓ Connected to MongoDB")
    return async_db


async def close_mongo():
    """Close MongoDB connection"""
    global async_client
    if async_client:
        async_client.close()
        print("✓ Disconnected from MongoDB")


def get_sync_mongo_db():
    """Get synchronous MongoDB database connection"""
    global sync_client, sync_db
    if not sync_client:
        sync_client = MongoClient(MONGO_URL)
        sync_db = sync_client[DATABASE_NAME]
    return sync_db


async def get_async_db():
    """Get async MongoDB database"""
    global async_db
    if async_db is None:
        await connect_to_mongo()
    return async_db

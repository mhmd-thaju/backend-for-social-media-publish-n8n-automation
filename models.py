from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PlatformEnum(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    BOTH = "both"
    LINKEDIN = "linkedin"


class MediaTypeEnum(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    STORY_IMAGE = "story_image"
    STORY_VIDEO = "story_video"
    LINKEDIN_TEXT = "linkedin_text"
    LINKEDIN_IMAGE = "linkedin_image"


class StatusEnum(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class ScheduledPost(BaseModel):
    """Model for scheduled social media posts"""
    media_type: MediaTypeEnum
    platform: PlatformEnum
    scheduled_time: datetime
    text_topic: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    status: StatusEnum = StatusEnum.SCHEDULED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PublishedPost(BaseModel):
    """Model for published posts history"""
    media_type: MediaTypeEnum
    platform: PlatformEnum
    text_topic: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    published_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_post_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Account(BaseModel):
    """Model for storing platform access tokens"""
    platform: PlatformEnum
    account_name: str
    page_access_token: Optional[str] = None
    user_access_token: Optional[str] = None
    token_expiry_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

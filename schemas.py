from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    name: str = Field(..., description="Full name")
    username: str = Field(..., description="Unique username")
    email: EmailStr = Field(..., description="Email address")
    bio: Optional[str] = Field(None, description="Short bio")
    profile_pic: Optional[HttpUrl] = Field(None, description="Profile picture URL")
    link: str = Field(..., description="Public profile link slug")

class Photo(BaseModel):
    image_url: HttpUrl = Field(..., description="Public URL to the image")
    caption: Optional[str] = Field(None, description="Photo caption")
    user_id: str = Field(..., description="Owner user id as string")
    is_public: bool = Field(True, description="Whether photo is publicly visible")
    date: datetime = Field(default_factory=datetime.utcnow, description="Upload date")

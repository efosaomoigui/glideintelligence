from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: Optional[str] = None
    username: str

class UserSchema(UserBase):
    id: int
    is_superuser: bool
    is_verified: bool
    auth_provider: str
    created_at: datetime
    class Config:
        from_attributes = True

class MagicLogin(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class GoogleAuth(BaseModel):
    token: str
    email: str
    name: str
    google_id: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

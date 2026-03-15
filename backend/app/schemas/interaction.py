from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from .user import UserBase

class CommentBase(BaseModel):
    content: str
    topic_id: Optional[int] = None
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class CommentSchema(CommentBase):
    id: int
    user_id: int
    created_at: datetime
    upvote_count: int = 0
    downvote_count: int = 0
    reply_count: int = 0
    is_featured: bool = False
    moderation_status: str = "pending"
    user: Optional[UserBase] = None
    
    model_config = ConfigDict(from_attributes=True)

class PollVoteBase(BaseModel):
    poll_option_id: int

class PollVoteCreate(PollVoteBase):
    pass

class PollVoteSchema(PollVoteBase):
    id: int
    user_id: int
    poll_id: int
    
    model_config = ConfigDict(from_attributes=True)

class PollOptionSchema(BaseModel):
    id: int
    poll_id: int
    option_text: str
    display_order: int
    vote_count: int

    model_config = ConfigDict(from_attributes=True)

class PollBase(BaseModel):
    question: str
    is_active: Optional[bool] = True

class PollCreate(PollBase):
    options: List[str]
    topic_id: Optional[int] = None
    poll_type: Optional[str] = "single_choice"
    closes_at: Optional[datetime] = None

class PollSchema(PollBase):
    id: int
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None
    created_at: datetime
    total_votes: int
    options: List[PollOptionSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

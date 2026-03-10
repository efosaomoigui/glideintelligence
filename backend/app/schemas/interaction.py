from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user import UserBase

class CommentBase(BaseModel):
    content: str
    article_id: Optional[int] = None
    topic_id: Optional[int] = None
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class CommentSchema(CommentBase):
    id: int
    user_id: int
    created_at: datetime
    user: Optional[UserBase] = None
    
    class Config:
        from_attributes = True

class PollVoteBase(BaseModel):
    poll_option_id: int

class PollVoteCreate(PollVoteBase):
    pass

class PollVoteSchema(PollVoteBase):
    id: int
    user_id: int
    poll_id: int
    
    class Config:
        from_attributes = True

class PollOptionSchema(BaseModel):
    id: int
    poll_id: int
    option_text: str
    display_order: int
    vote_count: int

    class Config:
        from_attributes = True

class PollBase(BaseModel):
    question: str
    is_active: Optional[bool] = True

class PollCreate(PollBase):
    options: List[str]
    topic_id: Optional[int] = None

class PollSchema(PollBase):
    id: int
    topic_id: Optional[int] = None
    created_at: datetime
    total_votes: int
    options: List[PollOptionSchema] = []
    
    class Config:
        from_attributes = True

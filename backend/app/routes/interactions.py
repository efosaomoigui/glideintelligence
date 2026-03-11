from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.interaction import Comment, Poll, PollVote, PollOption
from app.models.user import User
from app.schemas.interaction import CommentSchema, CommentCreate, PollSchema, PollCreate, PollVoteCreate, PollVoteSchema
from app.utils.auth_deps import get_current_active_user, get_current_active_superuser

router = APIRouter(prefix="/api/interactions", tags=["interactions"])

# --- Comments ---

@router.post("/comments", response_model=CommentSchema)
async def create_comment(
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comment_data = comment_in.model_dump()
    comment_data.pop("article_id", None)
    
    comment = Comment(
        **comment_data,
        user_id=current_user.id
    )
    db.add(comment)
    await db.commit()
    
    # Re-fetch with loaded user to avoid lazy-load crash in Pydantic serialization
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.id == comment.id)
    )
    comment = result.scalar_one()

    # Increment Topic comment_count atomically
    if comment_in.topic_id:
        from sqlalchemy import update as sql_update
        from app.models.topic import Topic
        await db.execute(
            sql_update(Topic)
            .where(Topic.id == comment_in.topic_id)
            .values(comment_count=Topic.comment_count + 1)
        )
        await db.commit()

    return comment

@router.get("/comments/topic/{topic_id}", response_model=List[CommentSchema])
async def get_topic_comments(topic_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.topic_id == topic_id)
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().all()

@router.get("/latest-comments", response_model=List[CommentSchema])
async def get_latest_comments(limit: int = 5, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

# --- Polls ---

@router.get("/polls", response_model=List[PollSchema])
async def get_active_polls(db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options))
        .where(Poll.is_active == True)
        .order_by(Poll.total_votes.desc(), Poll.created_at.desc())
    )
    return result.scalars().all()

@router.get("/polls/topic/{topic_id}")
async def get_topic_poll(
    topic_id: int, 
    user_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    # Get active poll for topic
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options).load_only(PollOption.id, PollOption.poll_id, PollOption.option_text, PollOption.vote_count, PollOption.display_order))
        .where(Poll.topic_id == topic_id, Poll.is_active == True)
        .order_by(Poll.created_at.desc())
    )
    poll = result.scalars().first()
    
    if not poll:
        return {"poll": None}
    
    poll_data = PollSchema.model_validate(poll).model_dump()
    
    # Check if user voted
    user_voted_option_id = None
    if user_id:
        vote_result = await db.execute(
            select(PollVote).where(
                PollVote.poll_id == poll.id,
                PollVote.user_id == user_id
            )
        )
        vote = vote_result.scalar_one_or_none()
        if vote:
            user_voted_option_id = vote.poll_option_id
            
    return {
        "poll": poll_data,
        "user_voted_option_id": user_voted_option_id
    }

@router.post("/polls/{poll_id}/vote", response_model=PollVoteSchema)
async def vote_in_poll(
    poll_id: int,
    vote_in: PollVoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if poll exists
    result = await db.execute(select(Poll).where(Poll.id == poll_id, Poll.is_active == True))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
        
    # Check if option exists
    result = await db.execute(select(PollOption).where(PollOption.id == vote_in.poll_option_id, PollOption.poll_id == poll_id))
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Poll option not found")
    
    # Check if already voted
    result = await db.execute(
        select(PollVote).where(
            PollVote.poll_id == poll_id,
            PollVote.user_id == current_user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already voted in this poll")
    
    # Create vote
    vote = PollVote(
        poll_id=poll_id,
        poll_option_id=vote_in.poll_option_id,
        user_id=current_user.id
    )
    db.add(vote)
    
    # Increment counts safely
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Poll)
        .where(Poll.id == poll_id)
        .values(total_votes=Poll.total_votes + 1)
    )
    await db.execute(
        sql_update(PollOption)
        .where(PollOption.id == vote_in.poll_option_id)
        .values(vote_count=PollOption.vote_count + 1)
    )
    
    await db.commit()
    
    # Re-fetch with loaded user/poll to avoid lazy-load crash
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(PollVote)
        .options(selectinload(PollVote.user))
        .where(PollVote.id == vote.id)
    )
    vote = result.scalar_one()
    return vote

# Admin: Create Poll
@router.post("/polls", response_model=PollSchema, dependencies=[Depends(get_current_active_superuser)])
async def create_poll(poll_in: PollCreate, db: AsyncSession = Depends(get_db)):
    poll_data = poll_in.model_dump(exclude={'options'})
    poll = Poll(**poll_data)
    db.add(poll)
    await db.flush() # flush to get poll id
    
    for idx, opt_text in enumerate(poll_in.options):
        opt = PollOption(poll_id=poll.id, option_text=opt_text, display_order=idx)
        db.add(opt)
        
    await db.commit()
    await db.refresh(poll)
    return poll

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.models import Job
import json

async def create_job_record(db: AsyncSession, job_type: str, payload: dict = None) -> int:
    """Create a new job record in the database."""
    import uuid
    job = Job(
        id=str(uuid.uuid4()),
        type=job_type,
        status="PENDING",
        payload=payload
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job.id

async def update_job_status(db: AsyncSession, job_id: str, status: str, result: dict = None, error: str = None):
    """Update the status of an existing job record."""
    values = {"status": status, "updated_at": datetime.utcnow()}
    if result:
        values["result"] = result
    if error:
        values["error"] = error
    
    if status in ["RUNNING", "STARTED"]:
        values["started_at"] = datetime.utcnow()
    elif status in ["COMPLETED", "SUCCESS", "FAILURE", "FAILED"]:
        values["completed_at"] = datetime.utcnow()
    
    stmt = update(Job).where(Job.id == job_id).values(**values)
    await db.execute(stmt)
    await db.commit()

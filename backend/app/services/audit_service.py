from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from typing import Optional

async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    target: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        target=target,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    await db.commit()

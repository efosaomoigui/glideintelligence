"""
Check audit logs in database
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.audit import AuditLog
from sqlalchemy import select, func

async def check_audit_logs():
    async with AsyncSessionLocal() as db:
        # Count total logs
        count_result = await db.execute(select(func.count()).select_from(AuditLog))
        count = count_result.scalar()
        print(f'Total audit logs in database: {count}')
        
        # Get recent logs
        result = await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
        )
        logs = result.scalars().all()
        
        print('\nRecent audit logs:')
        if logs:
            for log in logs:
                details = log.details[:50] if log.details else "No details"
                print(f'  {log.created_at} - {log.action} - {details}')
        else:
            print('  No audit logs found')

if __name__ == "__main__":
    asyncio.run(check_audit_logs())

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

async def seed_superuser():
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(select(User).where(User.email == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            await db.commit()
            print("Superuser 'admin' created successfully.")
        else:
            print("Superuser 'admin' already exists.")

if __name__ == "__main__":
    asyncio.run(seed_superuser())
